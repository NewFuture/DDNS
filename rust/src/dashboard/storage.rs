use std::fs::{self, OpenOptions};
use std::io::{self, Write};
use std::path::{Path, PathBuf};

use super::{Result, operation_error};

pub(super) fn target(path: &Path) -> Result<PathBuf> {
    let mut path = path.to_path_buf();
    for _ in 0..40 {
        match fs::symlink_metadata(&path) {
            Ok(metadata) if metadata.file_type().is_symlink() => {
                let link = fs::read_link(&path).map_err(operation_error)?;
                path = if link.is_absolute() {
                    link
                } else {
                    path.parent().unwrap_or(Path::new(".")).join(link)
                };
            }
            Ok(_) => return fs::canonicalize(path).map_err(operation_error),
            Err(error) if error.kind() == io::ErrorKind::NotFound => return Ok(path),
            Err(error) => return Err(operation_error(error)),
        }
    }
    Err(operation_error("too many symbolic links"))
}

pub(super) fn backup(path: &Path) -> PathBuf {
    let mut name = path.as_os_str().to_owned();
    name.push(".bak");
    PathBuf::from(name)
}

struct Temporary(PathBuf);
impl Temporary {
    fn new(directory: &Path, content: &[u8]) -> io::Result<Self> {
        for _ in 0..16 {
            let mut random = [0u8; 16];
            getrandom::fill(&mut random)
                .map_err(|_| io::Error::other("secure entropy unavailable"))?;
            let name = random
                .iter()
                .map(|byte| format!("{byte:02x}"))
                .collect::<String>();
            let path = directory.join(format!(".ddns-{name}.tmp"));
            let mut options = OpenOptions::new();
            options.write(true).create_new(true);
            #[cfg(unix)]
            {
                use std::os::unix::fs::OpenOptionsExt;
                options.mode(0o600);
            }
            match options.open(&path) {
                Ok(mut file) => {
                    let temporary = Self(path);
                    file.write_all(content)?;
                    file.sync_all()?;
                    return Ok(temporary);
                }
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => continue,
                Err(error) => return Err(error),
            }
        }
        Err(io::Error::new(
            io::ErrorKind::AlreadyExists,
            "unable to allocate a secure temporary file",
        ))
    }
    fn replace(&self, path: &Path) -> io::Result<()> {
        fs::rename(&self.0, path)
    }
}
impl Drop for Temporary {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.0);
    }
}

pub(super) fn write(path: &Path, content: &[u8]) -> Result<()> {
    let path = target(path)?;
    let directory = path.parent().unwrap_or(Path::new("."));
    fs::create_dir_all(directory).map_err(operation_error)?;
    let temporary = Temporary::new(directory, content).map_err(operation_error)?;
    match fs::read(&path) {
        Ok(previous) => {
            let saved = Temporary::new(directory, &previous).map_err(operation_error)?;
            let backup_path = backup(&path);
            let old_backup = match fs::read(&backup_path) {
                Ok(content) => Some(Temporary::new(directory, &content).map_err(operation_error)?),
                Err(error) if error.kind() == io::ErrorKind::NotFound => None,
                Err(error) => return Err(operation_error(error)),
            };
            commit_pair(&path, &temporary, &saved, old_backup.as_ref()).map_err(operation_error)?;
        }
        Err(error) if error.kind() == io::ErrorKind::NotFound => {
            temporary.replace(&path).map_err(operation_error)?
        }
        Err(error) => return Err(operation_error(error)),
    }
    sync_directory(directory);
    Ok(())
}

fn commit_pair(
    path: &Path,
    replacement: &Temporary,
    saved: &Temporary,
    old_backup: Option<&Temporary>,
) -> io::Result<()> {
    let backup_path = backup(path);
    saved.replace(&backup_path)?;
    if let Err(error) = replacement.replace(path) {
        if let Some(old_backup) = old_backup {
            old_backup.replace(&backup_path)?;
        } else {
            fs::remove_file(&backup_path)?;
        }
        return Err(error);
    }
    Ok(())
}

pub(super) fn restore(path: &Path, restored: &[u8]) -> Result<()> {
    let path = target(path)?;
    let directory = path.parent().unwrap_or(Path::new("."));
    let previous = match fs::read(&path) {
        Ok(content) => Some(Temporary::new(directory, &content).map_err(operation_error)?),
        Err(error) if error.kind() == io::ErrorKind::NotFound => None,
        Err(error) => return Err(operation_error(error)),
    };
    let replacement = Temporary::new(directory, restored).map_err(operation_error)?;
    replacement.replace(&path).map_err(operation_error)?;
    if let Some(previous) = previous
        && let Err(error) = previous.replace(&backup(&path))
    {
        // The backup commit failed; put the current file back before reporting failure.
        previous.replace(&path).map_err(operation_error)?;
        return Err(operation_error(error));
    }
    sync_directory(directory);
    Ok(())
}

fn sync_directory(directory: &Path) {
    #[cfg(unix)]
    if let Ok(file) = fs::File::open(directory) {
        let _ = file.sync_all();
    }
    #[cfg(not(unix))]
    let _ = directory;
}

#[cfg(test)]
mod tests {
    use std::fs;
    use std::time::{SystemTime, UNIX_EPOCH};

    use super::{Temporary, backup, commit_pair};

    #[test]
    fn failed_final_replacement_restores_original_backup() {
        let directory = std::env::temp_dir().join(format!(
            "ddns-backup-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir(&directory).unwrap();
        let path = directory.join("config.json");
        fs::create_dir(&path).unwrap();
        fs::write(path.join("occupied"), b"keep").unwrap();
        for previous in [Some(b"original backup".as_slice()), None] {
            let backup_path = backup(&path);
            let _ = fs::remove_file(&backup_path);
            if let Some(content) = previous {
                fs::write(&backup_path, content).unwrap();
            }
            let old_backup = previous.map(|content| Temporary::new(&directory, content).unwrap());
            let saved = Temporary::new(&directory, b"current").unwrap();
            let replacement = Temporary::new(&directory, b"replacement").unwrap();
            assert!(commit_pair(&path, &replacement, &saved, old_backup.as_ref()).is_err());
            assert_eq!(fs::read(&backup_path).ok().as_deref(), previous);
            assert_eq!(fs::read(path.join("occupied")).unwrap(), b"keep");
        }
        fs::remove_dir_all(directory).unwrap();
    }
}
