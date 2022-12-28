use lazy_static::lazy_static;
use std::{env, str::FromStr};

lazy_static! {
    pub static ref CONFIG: Config = Config {
        base_uri: get_env("BASE_URI"),
        bot_token: get_env("BOT_TOKEN"),
        bot_client_id: get_env_as("BOT_CLIENT_ID"),
        bot_client_secret: get_env("BOT_CLIENT_SECRET"),
        main_server: get_env_as("MAIN_SERVER"),
        premium1_role: get_env_as("PREMIUM1_ROLE"),
        premium3_role: get_env_as("PREMIUM3_ROLE"),
        premium5_role: get_env_as("PREMIUM5_ROLE"),
        payment_channel: get_env_as("PAYMENT_CHANNEL"),
        patron_channel: get_env_as("PATRON_CHANNEL"),
        api_host: get_env("API_HOST"),
        api_port: get_env_as("API_PORT"),
        api_workers: get_env_as("API_WORKERS"),
        api_secret: get_env("API_SECRET"),
        bot_api_host: get_env("BOT_API_HOST"),
        bot_api_port: get_env_as("BOT_API_PORT"),
        redis_host: get_env("REDIS_HOST"),
        redis_port: get_env_as("REDIS_PORT"),
        redis_password: get_env("REDIS_PASSWORD"),
    };
}

#[derive(Debug)]
pub struct Config {
    pub base_uri: String,
    pub bot_token: String,
    pub bot_client_id: u64,
    pub bot_client_secret: String,
    pub premium1_role: u64,
    pub premium3_role: u64,
    pub premium5_role: u64,
    pub main_server: u64,
    pub payment_channel: u64,
    pub patron_channel: u64,
    pub api_host: String,
    pub api_port: u16,
    pub api_workers: u64,
    pub api_secret: String,
    pub bot_api_host: String,
    pub bot_api_port: u16,
    pub redis_host: String,
    pub redis_port: u16,
    pub redis_password: String,
}

fn get_env(name: &str) -> String {
    env::var(name).unwrap_or_else(|_| panic!("Missing environmental variable: {}", name))
}

fn get_env_as<T: FromStr>(name: &str) -> T {
    get_env(name)
        .parse::<T>()
        .unwrap_or_else(|_| panic!("Invalid environmental variable: {}", name))
}
