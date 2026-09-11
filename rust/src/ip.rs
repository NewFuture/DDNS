use std::net::{IpAddr, Ipv4Addr, Ipv6Addr, SocketAddr, UdpSocket};
use std::process::Command;
use std::str::FromStr;

use regex::Regex;

use crate::error::{Error, Result};
use crate::http::{HttpClient, HttpRequest, redact_url};
use crate::logging::Logger;

const PUBLIC_IPV4_APIS: &[&str] = &[
    "https://api.ipify.org",
    "https://ipv4.ddnsip.cn",
    "https://ipinfo.io/ip",
    "https://api-ipv4.ip.sb/ip",
    "http://checkip.amazonaws.com",
];
const PUBLIC_IPV6_APIS: &[&str] = &[
    "https://api6.ipify.org/",
    "https://ipv6.ddnsip.cn",
    "https://api-ipv6.ip.sb/ip",
    "http://ipv6.icanhazip.com",
];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AddressFamily {
    V4,
    V6,
}

impl AddressFamily {
    pub const fn record_type(self) -> &'static str {
        match self {
            Self::V4 => "A",
            Self::V6 => "AAAA",
        }
    }

    const fn label(self) -> &'static str {
        match self {
            Self::V4 => "IPv4",
            Self::V6 => "IPv6",
        }
    }

    const fn matches(self, address: IpAddr) -> bool {
        matches!(
            (self, address),
            (Self::V4, IpAddr::V4(_)) | (Self::V6, IpAddr::V6(_))
        )
    }
}

pub fn resolve(
    family: AddressFamily,
    rules: &[String],
    client: &dyn HttpClient,
    logger: &Logger,
) -> Result<IpAddr> {
    let mut failures = Vec::new();
    for rule in rules {
        let displayed_rule = display_rule(rule);
        logger.debug(
            "ip",
            format!("trying {} rule `{displayed_rule}`", family.label()),
        );
        match resolve_rule(family, rule, client) {
            Ok(address) => {
                logger.info("ip", format!("resolved {} as {address}", family.label()));
                return Ok(address);
            }
            Err(error) => {
                logger.warning("ip", format!("rule `{displayed_rule}` failed: {error}"));
                failures.push(format!("{displayed_rule}: {error}"));
            }
        }
    }
    Err(Error::Ip(format!(
        "all {} rules failed: {}",
        family.label(),
        failures.join("; ")
    )))
}

fn display_rule(rule: &str) -> String {
    if let Some(url) = rule.strip_prefix("url:") {
        format!("url:{}", redact_url(url))
    } else if rule.starts_with("cmd:") {
        "cmd:<redacted>".to_owned()
    } else if rule.starts_with("shell:") {
        "shell:<redacted>".to_owned()
    } else {
        rule.to_owned()
    }
}

fn resolve_rule(family: AddressFamily, rule: &str, client: &dyn HttpClient) -> Result<IpAddr> {
    if let Ok(index) = rule.parse::<usize>() {
        return local_address(family, index);
    }
    if let Some(url) = rule.strip_prefix("url:") {
        return fetch_address(family, url, client);
    }
    if let Some(pattern) = rule.strip_prefix("regex:") {
        return regex_address(family, pattern);
    }
    if let Some(command) = rule.strip_prefix("cmd:") {
        return command_address(family, command, false);
    }
    if let Some(command) = rule.strip_prefix("shell:") {
        return command_address(family, command, true);
    }
    match rule {
        "default" => default_address(family),
        "public" => public_address(family, client),
        "local" => local_address(family, 0),
        _ => Err(Error::Ip("unknown address rule".to_owned())),
    }
}

fn default_address(family: AddressFamily) -> Result<IpAddr> {
    let (bind, remote) = match family {
        AddressFamily::V4 => (
            SocketAddr::new(IpAddr::V4(Ipv4Addr::UNSPECIFIED), 0),
            SocketAddr::new(IpAddr::V4(Ipv4Addr::new(1, 1, 1, 1)), 53),
        ),
        AddressFamily::V6 => (
            SocketAddr::new(IpAddr::V6(Ipv6Addr::UNSPECIFIED), 0),
            SocketAddr::new(
                IpAddr::V6(Ipv6Addr::from_str("2606:4700:4700::1111").expect("valid constant")),
                53,
            ),
        ),
    };
    let socket = UdpSocket::bind(bind)?;
    socket.connect(remote)?;
    let address = socket.local_addr()?.ip();
    validate_family(family, address)
}

fn local_address(family: AddressFamily, index: usize) -> Result<IpAddr> {
    select_local_address(
        family,
        index,
        if_addrs::get_if_addrs()?
            .into_iter()
            .map(|interface| interface.ip()),
    )
}

fn select_local_address(
    family: AddressFamily,
    index: usize,
    addresses: impl IntoIterator<Item = IpAddr>,
) -> Result<IpAddr> {
    let addresses = addresses
        .into_iter()
        .filter(|address| {
            family.matches(*address) && !address.is_loopback() && !address.is_unspecified()
        })
        .collect::<Vec<_>>();
    addresses.get(index).copied().ok_or_else(|| {
        Error::Ip(format!(
            "{} interface index {index} is unavailable ({} matching addresses)",
            family.label(),
            addresses.len()
        ))
    })
}

fn public_address(family: AddressFamily, client: &dyn HttpClient) -> Result<IpAddr> {
    let mut failures = Vec::new();
    let endpoints = match family {
        AddressFamily::V4 => PUBLIC_IPV4_APIS,
        AddressFamily::V6 => PUBLIC_IPV6_APIS,
    };
    for endpoint in endpoints {
        match fetch_address(family, endpoint, client) {
            Ok(address) => return Ok(address),
            Err(error) => failures.push(format!("{endpoint}: {error}")),
        }
    }
    Err(Error::Ip(failures.join("; ")))
}

fn fetch_address(family: AddressFamily, url: &str, client: &dyn HttpClient) -> Result<IpAddr> {
    let request = HttpRequest::get(url, Vec::new());
    let response = client.execute(&request)?;
    if !(200..300).contains(&response.status) {
        return Err(Error::Ip(format!(
            "HTTP {} {}",
            response.status, response.reason
        )));
    }
    extract_address(family, &response.body)
}

fn regex_address(family: AddressFamily, pattern: &str) -> Result<IpAddr> {
    let output = network_configuration()?;
    regex_address_in_text(family, pattern, &output)
}

fn regex_address_in_text(family: AddressFamily, pattern: &str, output: &str) -> Result<IpAddr> {
    let matcher = Regex::new(pattern).map_err(|error| {
        Error::Ip(format!(
            "invalid Rust regex pattern: {error}; regex: rules do not support Python look-around or backreferences"
        ))
    })?;
    for (address_text, address) in addresses_in_text(family, output) {
        if matcher
            .find(address_text)
            .is_some_and(|matched| matched.start() == 0)
        {
            return Ok(address);
        }
    }
    Err(Error::Ip("no local address matched the regex".to_owned()))
}

fn command_address(family: AddressFamily, command: &str, shell: bool) -> Result<IpAddr> {
    let output = if shell {
        shell_command(command)?
    } else {
        direct_command(command)?
    };
    extract_address(family, &output)
}

fn direct_command(command: &str) -> Result<String> {
    let arguments = split_command(command)?;
    let (program, arguments) = arguments
        .split_first()
        .ok_or_else(|| Error::Ip("cmd rule is empty".to_owned()))?;
    let output = Command::new(program).args(arguments).output()?;
    command_output(output)
}

#[cfg(windows)]
fn shell_command(command: &str) -> Result<String> {
    command_output(Command::new("cmd").args(["/C", command]).output()?)
}

#[cfg(not(windows))]
fn shell_command(command: &str) -> Result<String> {
    command_output(Command::new("/bin/sh").args(["-c", command]).output()?)
}

fn command_output(output: std::process::Output) -> Result<String> {
    if !output.status.success() {
        return Err(Error::Ip(format!(
            "command exited with {}: {}",
            output.status,
            String::from_utf8_lossy(&output.stderr).trim()
        )));
    }
    String::from_utf8(output.stdout)
        .map_err(|error| Error::Ip(format!("command output is not UTF-8: {error}")))
}

fn network_configuration() -> Result<String> {
    #[cfg(windows)]
    let candidates: &[(&str, &[&str])] = &[("ipconfig", &[])];
    #[cfg(not(windows))]
    let candidates: &[(&str, &[&str])] = &[("ip", &["address"]), ("ifconfig", &[])];

    let mut errors = Vec::new();
    for (program, arguments) in candidates {
        match Command::new(program).args(*arguments).output() {
            Ok(output) if output.status.success() => {
                return Ok(String::from_utf8_lossy(&output.stdout).into_owned());
            }
            Ok(output) => errors.push(format!("{program}: {}", output.status)),
            Err(error) => errors.push(format!("{program}: {error}")),
        }
    }
    Err(Error::Ip(format!(
        "unable to read network configuration: {}",
        errors.join("; ")
    )))
}

fn extract_address(family: AddressFamily, content: &str) -> Result<IpAddr> {
    addresses_in_text(family, content)
        .next()
        .map(|(_, address)| address)
        .ok_or_else(|| Error::Ip(format!("response contains no valid {}", family.label())))
}

fn addresses_in_text(
    family: AddressFamily,
    content: &str,
) -> impl Iterator<Item = (&str, IpAddr)> + '_ {
    content
        .split(|character: char| {
            character.is_whitespace()
                || matches!(
                    character,
                    ',' | ';' | '=' | '[' | ']' | '(' | ')' | '<' | '>' | '"' | '\''
                )
        })
        .filter_map(move |token| {
            let token = token
                .trim_matches(['/', '%', '.'])
                .split(['/', '%'])
                .next()
                .unwrap_or_default();
            // A hex prefix can be part of IPv6; only strip unambiguous text labels.
            let token = match token.split_once(':') {
                Some((label, address))
                    if label
                        .bytes()
                        .all(|byte| byte.is_ascii_alphanumeric() || byte == b'_')
                        && label.bytes().any(|byte| !byte.is_ascii_hexdigit()) =>
                {
                    address
                }
                _ => token,
            };
            token
                .parse::<IpAddr>()
                .ok()
                .filter(|address| family.matches(*address))
                .map(|address| (token, address))
        })
}

fn validate_family(family: AddressFamily, address: IpAddr) -> Result<IpAddr> {
    if family.matches(address) {
        Ok(address)
    } else {
        Err(Error::Ip(format!(
            "{address} is not a valid {} address",
            family.label()
        )))
    }
}

fn split_command(command: &str) -> Result<Vec<String>> {
    let mut arguments = Vec::new();
    let mut current = String::new();
    let mut quote = None;
    let mut escaped = false;
    for character in command.chars() {
        if escaped {
            current.push(character);
            escaped = false;
            continue;
        }
        if character == '\\' && !cfg!(windows) {
            escaped = true;
            continue;
        }
        if let Some(active_quote) = quote {
            if character == active_quote {
                quote = None;
            } else {
                current.push(character);
            }
            continue;
        }
        if matches!(character, '"' | '\'') {
            quote = Some(character);
        } else if character.is_whitespace() {
            if !current.is_empty() {
                arguments.push(std::mem::take(&mut current));
            }
        } else if matches!(character, '|' | ';' | '&' | '>' | '<') {
            return Err(Error::Ip(
                "cmd rules cannot contain shell operators; use shell: explicitly".to_owned(),
            ));
        } else {
            current.push(character);
        }
    }
    if escaped || quote.is_some() {
        return Err(Error::Ip("unterminated cmd quoting".to_owned()));
    }
    if !current.is_empty() {
        arguments.push(current);
    }
    Ok(arguments)
}

#[cfg(test)]
mod tests {
    use std::path::Path;

    use crate::error::Result;
    use crate::http::{HttpClient, HttpRequest, HttpResponse};
    use crate::logging::{Level, Logger};

    use super::{
        AddressFamily, command_address, default_address, extract_address, local_address,
        regex_address_in_text, resolve, select_local_address, split_command,
    };

    struct FakeClient;

    impl HttpClient for FakeClient {
        fn execute(&self, request: &HttpRequest) -> Result<HttpResponse> {
            let body = if request.url.contains("invalid") {
                "address unavailable"
            } else {
                "current address: 192.0.2.44"
            };
            Ok(HttpResponse {
                status: 200,
                reason: "OK".to_owned(),
                body: body.to_owned(),
            })
        }
    }

    #[test]
    fn local_address_indices_skip_loopback_and_unspecified() {
        let addresses = [
            "127.0.0.1",
            "::1",
            "0.0.0.0",
            "::",
            "192.168.1.2",
            "fd00::1",
            "127.2.3.4",
            "192.0.2.10",
            "fe80::2",
        ]
        .map(|address| address.parse::<std::net::IpAddr>().unwrap());
        for (family, expected) in [
            (AddressFamily::V4, ["192.168.1.2", "192.0.2.10"]),
            (AddressFamily::V6, ["fd00::1", "fe80::2"]),
        ] {
            for (index, expected) in expected.iter().enumerate() {
                assert_eq!(
                    select_local_address(family, index, addresses)
                        .unwrap()
                        .to_string(),
                    *expected
                );
            }
            let error = select_local_address(family, 2, addresses).unwrap_err();
            assert!(error.to_string().contains("2 matching addresses"));
        }
    }

    #[test]
    fn local_address_index_errors_without_usable_candidates() {
        let addresses = ["127.0.0.1", "127.2.3.4", "0.0.0.0", "::1", "::"]
            .map(|address| address.parse::<std::net::IpAddr>().unwrap());
        for family in [AddressFamily::V4, AddressFamily::V6] {
            for candidates in [addresses.as_slice(), &[]] {
                let error =
                    select_local_address(family, 0, candidates.iter().copied()).unwrap_err();
                assert!(error.to_string().contains("0 matching addresses"));
            }
        }
    }

    #[test]
    fn extracts_only_requested_address_family() {
        let content = "IPv6 2001:db8::1 and IPv4 192.0.2.1";
        assert_eq!(
            extract_address(AddressFamily::V4, content)
                .unwrap()
                .to_string(),
            "192.0.2.1"
        );
        assert_eq!(
            extract_address(AddressFamily::V6, content)
                .unwrap()
                .to_string(),
            "2001:db8::1"
        );
    }

    #[test]
    fn extracts_addresses_at_the_end_of_sentences() {
        for (family, content, expected) in [
            (AddressFamily::V4, "Current IP: 192.0.2.1.", "192.0.2.1"),
            (AddressFamily::V6, "Current IP: 2001:db8::1.", "2001:db8::1"),
        ] {
            assert_eq!(
                extract_address(family, content).unwrap().to_string(),
                expected
            );
        }
    }

    #[test]
    fn extracts_labeled_addresses_without_truncating_ipv6() {
        for address in [
            "::",
            "::1",
            "2001:db8::1",
            "2001:db8:0:1:2:3:4:5",
            "2001:db8::192.0.2.10",
            "::ffff:192.0.2.10",
            "::192.0.2.10",
            "2001:db8:0:1:2:3:192.0.2.10",
            "2001:db8:0:1::192.0.2.10",
            "2001:db8:0:1:2::192.0.2.10",
            "2001:db8::1:2:192.0.2.10",
            "2001:DB8::192.0.2.10",
            "dead:2001:db8::1",
        ] {
            let expected = address.parse::<std::net::IpAddr>().unwrap();
            for label in ["", "IP:", "address:", "IPv6:"] {
                let content = format!("{label}{address}.");
                assert_eq!(
                    extract_address(AddressFamily::V6, &content).unwrap(),
                    expected,
                    "{content}"
                );
            }
        }
        assert_eq!(
            extract_address(AddressFamily::V4, "IP:192.0.2.10")
                .unwrap()
                .to_string(),
            "192.0.2.10"
        );
    }

    #[test]
    fn rejects_invalid_address_fragments_even_with_labels() {
        for address in [
            "2001:db8::192.0.2.999",
            "2001:db8:0:0:0:0:0:0:1",
            "2001:db8:::1",
            ":2001:db8::1",
            "2001:db8::1:",
            ":::1",
            "2001.0:db8::1",
            "192.0.2.10",
        ] {
            for label in ["", "IP:", "address:"] {
                let content = format!("{label}{address}");
                assert!(
                    extract_address(AddressFamily::V6, &content).is_err(),
                    "{content}"
                );
            }
        }
        assert!(extract_address(AddressFamily::V4, "IP:192.0.2.999").is_err());
        assert!(extract_address(AddressFamily::V4, "IP:::ffff:192.0.2.10").is_err());
    }

    #[test]
    fn preserves_scoped_and_cidr_addresses() {
        for (family, content, expected) in [
            (AddressFamily::V4, "inet 192.0.2.10/24", "192.0.2.10"),
            (AddressFamily::V6, "inet6 2001:db8::1/64", "2001:db8::1"),
            (AddressFamily::V6, "[fe80::1%eth0]", "fe80::1"),
        ] {
            assert_eq!(
                extract_address(family, content).unwrap().to_string(),
                expected
            );
        }
    }

    #[test]
    fn parses_direct_commands_without_shell_operators() {
        assert_eq!(
            split_command(r#"program --name "two words""#).unwrap(),
            vec!["program", "--name", "two words"]
        );
        assert!(split_command("program | other").is_err());

        #[cfg(windows)]
        assert_eq!(
            split_command(r#""C:\Program Files\Tool\tool.exe" --flag"#).unwrap(),
            vec![r"C:\Program Files\Tool\tool.exe", "--flag"]
        );
    }

    #[test]
    fn resolves_url_fallback_and_public_rules() {
        let logger = Logger::new(Level::Critical, None::<&Path>, Vec::new()).unwrap();
        let address = resolve(
            AddressFamily::V4,
            &[
                "url:http://test/invalid".to_owned(),
                "url:http://test/valid".to_owned(),
            ],
            &FakeClient,
            &logger,
        )
        .unwrap();
        assert_eq!(address.to_string(), "192.0.2.44");

        let public = resolve(
            AddressFamily::V4,
            &["public".to_owned()],
            &FakeClient,
            &logger,
        )
        .unwrap();
        assert_eq!(public.to_string(), "192.0.2.44");
    }

    #[test]
    fn resolves_default_local_regex_and_command_rules() {
        assert!(matches!(
            default_address(AddressFamily::V4).unwrap(),
            std::net::IpAddr::V4(_)
        ));
        assert!(matches!(
            local_address(AddressFamily::V4, 0).unwrap(),
            std::net::IpAddr::V4(_)
        ));
        assert_eq!(
            regex_address_in_text(
                AddressFamily::V4,
                r"192\.168\..*",
                "inet 10.0.0.1/8\ninet 192.168.1.2/24"
            )
            .unwrap()
            .to_string(),
            "192.168.1.2"
        );

        #[cfg(windows)]
        let command = "cmd.exe /C echo 192.0.2.55";
        #[cfg(not(windows))]
        let command = "printf 192.0.2.55";
        assert_eq!(
            command_address(AddressFamily::V4, command, false)
                .unwrap()
                .to_string(),
            "192.0.2.55"
        );
    }

    #[test]
    fn reports_python_only_regex_features_clearly() {
        for pattern in [r"192\.168\.(?!0\.).*", r"(\d)\1"] {
            let error =
                regex_address_in_text(AddressFamily::V4, pattern, "inet 192.168.1.2").unwrap_err();
            let message = error.to_string();
            assert!(message.contains("invalid Rust regex pattern"));
            assert!(message.contains("look-around or backreferences"));
        }
    }

    #[test]
    fn regex_rules_match_only_from_address_start() {
        assert!(
            regex_address_in_text(AddressFamily::V4, r"192\.168", "inet 10.192.168.1/24").is_err()
        );
        assert_eq!(
            regex_address_in_text(AddressFamily::V4, r"10\.192", "inet 10.192.168.1/24")
                .unwrap()
                .to_string(),
            "10.192.168.1"
        );
    }

    #[test]
    fn regex_rules_preserve_ipv6_spelling() {
        for (pattern, output, expected) in [
            ("^2001:0db8:", "inet6 2001:0db8::1/64", "2001:db8::1"),
            (
                "^2001:0db8:0000:0000:0000:0000:0000:0001$",
                "inet6 2001:0db8:0000:0000:0000:0000:0000:0001/64",
                "2001:db8::1",
            ),
            ("^2001:0DB8::AbCd$", "IP:2001:0DB8::AbCd", "2001:db8::abcd"),
            ("^FE80::0001$", "IPv6 Address: [FE80::0001%eth0]", "fe80::1"),
            (
                r"^2001:0db8::192\.0\.2\.10$",
                "inet6 2001:0db8::192.0.2.10/96",
                "2001:db8::c000:20a",
            ),
        ] {
            assert_eq!(
                regex_address_in_text(AddressFamily::V6, pattern, output)
                    .unwrap()
                    .to_string(),
                expected,
                "{output}"
            );
        }
    }

    #[test]
    fn regex_rules_do_not_match_reformatted_ipv6() {
        for output in ["inet6 2001:0db8::1/64", "inet6 2001:DB8::1/64"] {
            assert!(
                regex_address_in_text(AddressFamily::V6, "^2001:db8::1$", output).is_err(),
                "{output}"
            );
        }
    }

    #[test]
    fn regex_rules_skip_invalid_and_other_family_candidates() {
        let output = "inet6 2001:0db8:::1/64\ninet 192.0.2.10/24";
        assert!(regex_address_in_text(AddressFamily::V6, ".*", output).is_err());
        assert_eq!(
            regex_address_in_text(AddressFamily::V4, ".*", output)
                .unwrap()
                .to_string(),
            "192.0.2.10"
        );
        assert_eq!(
            regex_address_in_text(
                AddressFamily::V6,
                "^2001:0db8:",
                &format!("{output}\ninet6 2001:0db8::2/64"),
            )
            .unwrap()
            .to_string(),
            "2001:db8::2"
        );
    }
}
