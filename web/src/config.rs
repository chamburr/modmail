use lazy_static::lazy_static;
use serde::Deserialize;
use std::{env, str::FromStr};

lazy_static! {
    pub static ref CONFIG: Config = Config {
        base_uri: get_env("BASE_URI"),
        environment: get_env_as("ENVIRONMENT"),
        sentry_dsn: get_env("SENTRY_DSN"),
        bot_client_id: get_env_as("BOT_CLIENT_ID"),
        bot_client_secret: get_env("BOT_CLIENT_SECRET"),
        api_host: get_env("API_HOST"),
        api_port: get_env_as("API_PORT"),
        api_workers: get_env_as("API_WORKERS"),
        api_secret: get_env("API_SECRET"),
        bot_host: get_env("BOT_API_HOST"),
        bot_port: get_env_as("BOT_API_PORT"),
        redis_host: get_env("REDIS_HOST"),
        redis_port: get_env_as("REDIS_PORT"),
        redis_password: get_env("REDIS_PASSWORD"),
    };
}

#[derive(Debug, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum Environment {
    Development,
    Production,
}

impl FromStr for Environment {
    type Err = serde_json::error::Error;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        serde_json::from_str(format!("\"{}\"", s).as_str())
    }
}

#[derive(Debug)]
pub struct Config {
    pub base_uri: String,
    pub environment: Environment,
    pub sentry_dsn: String,
    pub bot_client_id: u64,
    pub bot_client_secret: String,
    pub api_host: String,
    pub api_port: u16,
    pub api_workers: u64,
    pub api_secret: String,
    pub bot_host: String,
    pub bot_port: u16,
    pub redis_host: String,
    pub redis_port: u16,
    pub redis_password: String,
}

fn get_env(name: &str) -> String {
    env::var(name).unwrap_or_else(|_| panic!("Missing environmental variable: {}", name))
}

fn get_env_as<T>(name: &str) -> T
where
    T: std::str::FromStr,
    <T as std::str::FromStr>::Err: std::fmt::Debug,
{
    get_env(name)
        .parse::<T>()
        .unwrap_or_else(|_| panic!("Invalid environmental variable: {}", name))
}
