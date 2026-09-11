use std::collections::BTreeMap;

use hmac::{Hmac, KeyInit, Mac};
use sha2::{Digest, Sha256};
use time::OffsetDateTime;

use crate::error::{Error, Result};

type HmacSha256 = Hmac<Sha256>;

pub(crate) fn acs_timestamp() -> String {
    let now = OffsetDateTime::now_utc();
    format!(
        "{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z",
        now.year(),
        u8::from(now.month()),
        now.day(),
        now.hour(),
        now.minute(),
        now.second()
    )
}

pub(crate) fn request_nonce() -> Result<String> {
    let mut bytes = [0_u8; 16];
    getrandom::fill(&mut bytes)
        .map_err(|error| Error::Provider(format!("failed to generate request nonce: {error}")))?;
    Ok(hex_lower(&bytes))
}

pub fn sha256_hex(data: impl AsRef<[u8]>) -> String {
    hex_lower(&Sha256::digest(data.as_ref()))
}

pub fn hmac_sha256_hex(key: impl AsRef<[u8]>, message: impl AsRef<[u8]>) -> Result<String> {
    let mut mac = HmacSha256::new_from_slice(key.as_ref())
        .map_err(|error| Error::Provider(format!("invalid HMAC key: {error}")))?;
    mac.update(message.as_ref());
    Ok(hex_lower(&mac.finalize().into_bytes()))
}

pub fn hmac_sha256(key: impl AsRef<[u8]>, message: impl AsRef<[u8]>) -> Result<Vec<u8>> {
    let mut mac = HmacSha256::new_from_slice(key.as_ref())
        .map_err(|error| Error::Provider(format!("invalid HMAC key: {error}")))?;
    mac.update(message.as_ref());
    Ok(mac.finalize().into_bytes().to_vec())
}

#[allow(clippy::too_many_arguments)]
pub fn hmac_sha256_authorization(
    secret: impl AsRef<[u8]>,
    algorithm: &str,
    timestamp: &str,
    credential: &str,
    method: &str,
    path: &str,
    query: &str,
    headers: &BTreeMap<String, String>,
    body_hash: &str,
) -> Result<String> {
    let (canonical_request, signed_headers) =
        canonical_request(method, path, query, headers, body_hash);
    let string_to_sign = format!(
        "{algorithm}\n{timestamp}\n{}",
        sha256_hex(canonical_request)
    );
    let signature = hmac_sha256_hex(secret, string_to_sign)?;
    Ok(format!(
        "{algorithm} {credential}, SignedHeaders={signed_headers}, Signature={signature}"
    ))
}

#[allow(clippy::too_many_arguments)]
pub fn tc3_authorization(
    secret: impl AsRef<[u8]>,
    timestamp: &str,
    access_key_id: &str,
    scope: &str,
    method: &str,
    path: &str,
    query: &str,
    headers: &BTreeMap<String, String>,
    body_hash: &str,
) -> Result<String> {
    let (canonical_request, signed_headers) =
        canonical_request(method, path, query, headers, body_hash);
    let string_to_sign = format!(
        "TC3-HMAC-SHA256\n{timestamp}\n{scope}\n{}",
        sha256_hex(canonical_request)
    );
    let signature = hmac_sha256_hex(secret, string_to_sign)?;
    Ok(format!(
        "TC3-HMAC-SHA256 Credential={access_key_id}/{scope}, SignedHeaders={signed_headers}, Signature={signature}"
    ))
}

pub fn acs3_authorization(
    access_key_id: &str,
    secret: &str,
    method: &str,
    path: &str,
    query: &str,
    headers: &BTreeMap<String, String>,
    body_hash: &str,
) -> Result<String> {
    let (canonical_request, signed_headers) =
        canonical_request(method, path, query, headers, body_hash);
    let string_to_sign = format!("ACS3-HMAC-SHA256\n{}", sha256_hex(canonical_request));
    let signature = hmac_sha256_hex(secret, string_to_sign)?;
    Ok(format!(
        "ACS3-HMAC-SHA256 Credential={access_key_id},SignedHeaders={signed_headers},Signature={signature}"
    ))
}

fn canonical_request(
    method: &str,
    path: &str,
    query: &str,
    headers: &BTreeMap<String, String>,
    body_hash: &str,
) -> (String, String) {
    let normalized = headers
        .iter()
        .map(|(name, value)| (name.to_ascii_lowercase(), value.trim().to_owned()))
        .collect::<BTreeMap<_, _>>();
    let canonical_headers = normalized
        .iter()
        .map(|(name, value)| format!("{name}:{value}\n"))
        .collect::<String>();
    let signed_headers = normalized.keys().cloned().collect::<Vec<_>>().join(";");
    let canonical_request = format!(
        "{}\n{path}\n{query}\n{canonical_headers}\n{signed_headers}\n{body_hash}",
        method.to_ascii_uppercase()
    );
    (canonical_request, signed_headers)
}

fn hex_lower(bytes: &[u8]) -> String {
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        output.push(hex_digit(byte >> 4));
        output.push(hex_digit(byte & 0x0f));
    }
    output
}

const fn hex_digit(value: u8) -> char {
    match value {
        0..=9 => (b'0' + value) as char,
        _ => (b'a' + value - 10) as char,
    }
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeMap;

    use super::{acs3_authorization, sha256_hex, tc3_authorization};

    #[test]
    fn hashes_known_vector() {
        assert_eq!(
            sha256_hex("abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
    }

    #[test]
    fn signs_deterministically() {
        let headers = BTreeMap::from([
            ("host".to_owned(), "alidns.aliyuncs.com".to_owned()),
            (
                "x-acs-content-sha256".to_owned(),
                sha256_hex("DomainName=example.com"),
            ),
            ("x-acs-date".to_owned(), "2024-01-01T00:00:00Z".to_owned()),
        ]);
        let signature = acs3_authorization(
            "test-id",
            "test-secret",
            "POST",
            "/",
            "",
            &headers,
            &sha256_hex("DomainName=example.com"),
        )
        .unwrap();
        assert_eq!(
            signature,
            "ACS3-HMAC-SHA256 Credential=test-id,SignedHeaders=host;x-acs-content-sha256;x-acs-date,Signature=1b2814647ddf27f425cb6319c8973d72d998188eb84357279a0d2af3a1b77c23"
        );
    }

    #[test]
    fn tc3_signature_includes_credential_scope() {
        let headers = BTreeMap::from([
            ("content-type".to_owned(), "application/json".to_owned()),
            ("host".to_owned(), "dnspod.tencentcloudapi.com".to_owned()),
        ]);
        let authorization = tc3_authorization(
            b"derived-signing-key",
            "1700000000",
            "secret-id",
            "2023-11-14/dnspod/tc3_request",
            "POST",
            "/",
            "",
            &headers,
            &sha256_hex("{}"),
        )
        .unwrap();
        assert!(authorization.contains("Credential=secret-id/2023-11-14/dnspod/tc3_request"));
        assert_eq!(
            authorization,
            "TC3-HMAC-SHA256 Credential=secret-id/2023-11-14/dnspod/tc3_request, SignedHeaders=content-type;host, Signature=97ab304556363150d2c72f6f983edc9782cd1eead94e72a13b0d56c7d472e91d"
        );
    }
}
