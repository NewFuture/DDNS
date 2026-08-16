use std::fmt::{self, Display, Formatter};

pub type Result<T> = std::result::Result<T, Error>;

#[derive(Debug)]
pub enum Error {
    Usage(String),
    Config(String),
    Unsupported(String),
    Io(std::io::Error),
    Json(serde_json::Error),
    Http(String),
    Ip(String),
    Cache(String),
    Provider(String),
}

impl Error {
    pub const fn exit_code(&self) -> i32 {
        match self {
            Self::Usage(_) | Self::Config(_) | Self::Unsupported(_) => 2,
            Self::Io(_)
            | Self::Json(_)
            | Self::Http(_)
            | Self::Ip(_)
            | Self::Cache(_)
            | Self::Provider(_) => 1,
        }
    }
}

impl Display for Error {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> fmt::Result {
        match self {
            Self::Usage(message)
            | Self::Config(message)
            | Self::Unsupported(message)
            | Self::Http(message)
            | Self::Ip(message)
            | Self::Cache(message)
            | Self::Provider(message) => formatter.write_str(message),
            Self::Io(error) => Display::fmt(error, formatter),
            Self::Json(error) => Display::fmt(error, formatter),
        }
    }
}

impl std::error::Error for Error {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::Io(error) => Some(error),
            Self::Json(error) => Some(error),
            _ => None,
        }
    }
}

impl From<std::io::Error> for Error {
    fn from(error: std::io::Error) -> Self {
        Self::Io(error)
    }
}

impl From<serde_json::Error> for Error {
    fn from(error: serde_json::Error) -> Self {
        Self::Json(error)
    }
}
