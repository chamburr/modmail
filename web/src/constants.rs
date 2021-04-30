pub const COOKIE_NAME: &str = "session";
pub const CALLBACK_PATH: &str = "/callback";

pub const CSRF_TOKEN_KEY: &str = "csrf_token";
pub const STATS_KEY: &str = "bot_stats";
pub const STATUS_KEY: &str = "gateway_statuses";
pub const USER_TOKEN_KEY: &str = "user_token";

pub const CSRF_TOKEN_KEY_TTL: usize = 300000;
pub const USER_GUILDS_KEY_TTL: usize = 10000;

pub fn csrf_token_key(id: &str) -> String {
    format!("{}:{}", CSRF_TOKEN_KEY, id)
}

pub fn user_token_key(id: u64) -> String {
    format!("{}:{}", USER_TOKEN_KEY, id)
}
