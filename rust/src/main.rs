fn main() {
    if let Err(error) = ddns_rs::run_from(std::env::args_os()) {
        eprintln!("ddns-rs: {error}");
        std::process::exit(error.exit_code());
    }
}
