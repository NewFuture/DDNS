use std::collections::BTreeMap;

use ddns_rs::cli::CliOptions;
use ddns_rs::config::{AddressRules, TlsMode, load};
use serde_json::{Value, json};

#[test]
fn loads_remote_jsonc_multi_provider_with_cli_and_env_precedence() {
    let cli = CliOptions {
        values: BTreeMap::from([("ttl".to_owned(), json!(900))]),
        config_paths: Some(vec!["https://config.example.test/ddns.json".to_owned()]),
        new_config: None,
    };
    let environment = BTreeMap::from([
        ("ttl".to_owned(), json!("600")),
        ("cache".to_owned(), json!("false")),
        ("index6".to_owned(), json!("false")),
    ]);
    let document = r#"{
        // global settings
        "ttl": 300,
        "ssl": "auto",
        "providers": [
            {
                "provider": "cloudflare",
                "token": "cf-token",
                "ipv4": ["cf.example.com"],
                "index4": "public",
                "extra": {"proxied": true}
            },
            {
                "provider": "dnspod",
                "id": "12345",
                "token": "dp-token",
                "ipv4": "dp.example.com",
                "index4": ["default"]
            }
        ]
    }"#;
    let configs = load(&cli, &environment, &|url| {
        assert_eq!(url, "https://config.example.test/ddns.json");
        Ok(document.to_owned())
    })
    .unwrap();

    assert_eq!(configs.len(), 2);
    assert_eq!(configs[0].provider, "cloudflare");
    assert_eq!(configs[0].ttl, Some(900));
    assert_eq!(configs[0].ipv4, vec!["cf.example.com"]);
    assert_eq!(configs[0].extra["proxied"], Value::Bool(true));
    assert_eq!(configs[0].tls, TlsMode::Auto);
    assert_eq!(configs[1].provider, "dnspod");
    assert_eq!(configs[1].id, "12345");
    assert_eq!(configs[1].index6, AddressRules::Disabled);
}

#[test]
fn loads_python_literal_configuration_without_executing_code() {
    let cli = CliOptions {
        values: BTreeMap::new(),
        config_paths: Some(vec!["legacy.conf".to_owned()]),
        new_config: None,
    };
    let content = "{'dns': 'debug', 'index4': False, 'ipv4': ['a.example.com'],}";
    let path =
        std::env::temp_dir().join(format!("ddns-rs-config-{}-legacy.conf", std::process::id()));
    std::fs::write(&path, content).unwrap();
    let mut cli = cli;
    cli.config_paths = Some(vec![path.display().to_string()]);
    let configs = load(&cli, &BTreeMap::new(), &|_| unreachable!()).unwrap();
    assert_eq!(configs[0].provider, "debug");
    assert_eq!(configs[0].index4, AddressRules::Disabled);
    let _ = std::fs::remove_file(path);
}

#[test]
fn string_false_disables_env_address_lists() {
    let cli = CliOptions {
        values: BTreeMap::from([("dns".to_owned(), json!("debug"))]),
        config_paths: None,
        new_config: None,
    };
    let environment = BTreeMap::from([
        ("ipv4".to_owned(), json!("false")),
        ("index4".to_owned(), json!("false")),
    ]);
    let configs = load(&cli, &environment, &|_| unreachable!()).unwrap();
    assert!(configs[0].ipv4.is_empty());
    assert_eq!(configs[0].index4, AddressRules::Disabled);
}

#[test]
fn rejects_documents_without_provider_entries() {
    for document in ["[]", r#"{"providers":[]}"#] {
        let cli = CliOptions {
            values: BTreeMap::new(),
            config_paths: Some(vec!["https://config.example/empty.json".to_owned()]),
            new_config: None,
        };
        let error = load(&cli, &BTreeMap::new(), &|_| Ok(document.to_owned())).unwrap_err();
        assert!(
            error
                .to_string()
                .contains("does not contain any provider entries")
        );
    }
}

#[test]
fn empty_cli_config_list_overrides_environment_config_path() {
    let cli = CliOptions {
        values: BTreeMap::from([("dns".to_owned(), json!("debug"))]),
        config_paths: Some(Vec::new()),
        new_config: None,
    };
    let environment = BTreeMap::from([(
        "config".to_owned(),
        json!("https://environment.example/config.json"),
    )]);
    let configs = load(&cli, &environment, &|_| {
        panic!("environment config must not be fetched")
    })
    .unwrap();
    assert_eq!(configs.len(), 1);
    assert_eq!(configs[0].provider, "debug");
}

#[test]
fn debug_provider_fallback_requires_cli_debug_without_loaded_file() {
    let environment_debug = BTreeMap::from([("debug".to_owned(), json!("true"))]);
    let no_cli_debug = CliOptions {
        values: BTreeMap::new(),
        config_paths: Some(Vec::new()),
        new_config: None,
    };
    assert!(load(&no_cli_debug, &environment_debug, &|_| unreachable!()).is_err());

    let cli_debug = CliOptions {
        values: BTreeMap::from([("debug".to_owned(), json!(true))]),
        config_paths: Some(Vec::new()),
        new_config: None,
    };
    let configs = load(&cli_debug, &BTreeMap::new(), &|_| unreachable!()).unwrap();
    assert_eq!(configs[0].provider, "debug");

    let cli_debug_with_file = CliOptions {
        values: BTreeMap::from([("debug".to_owned(), json!(true))]),
        config_paths: Some(vec!["https://config.example/no-provider.json".to_owned()]),
        new_config: None,
    };
    assert!(
        load(&cli_debug_with_file, &BTreeMap::new(), &|_| Ok(
            "{}".to_owned()
        ))
        .is_err()
    );
}

#[test]
fn callback_object_token_survives_normal_file_loading() {
    let cli = CliOptions {
        values: BTreeMap::new(),
        config_paths: Some(vec!["https://config.example/callback.json".to_owned()]),
        new_config: None,
    };
    let document = r#"{
        "dns": "callback",
        "id": "https://callback.example/update",
        "token": {"api_key": "secret", "address": "__IP__"}
    }"#;
    let configs = load(&cli, &BTreeMap::new(), &|_| Ok(document.to_owned())).unwrap();
    assert_eq!(
        serde_json::from_str::<Value>(&configs[0].token).unwrap(),
        json!({"api_key": "secret", "address": "__IP__"})
    );
}
