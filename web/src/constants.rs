pub const COOKIE_NAME: &str = "session";
pub const CALLBACK_PATH: &str = "/callback";

pub const CSRF_TOKEN_KEY: &str = "csrf_token";
pub const STATS_KEY: &str = "bot_stats";
pub const STATUS_KEY: &str = "gateway_statuses";
pub const TOKEN_KEY: &str = "token";
pub const TOKEN_INFO_KEY: &str = "token_info";

pub const CSRF_TOKEN_KEY_TTL: usize = 300000;
pub const TOKEN_INFO_KEY_TTL: usize = 60000;

pub fn csrf_token_key(id: &str) -> String {
    format!("{}:{}", CSRF_TOKEN_KEY, id)
}

pub fn token_key(id: u64) -> String {
    format!("{}:{}", TOKEN_KEY, id)
}

pub fn token_info_key(id: &str) -> String {
    format!("{}:{}", TOKEN_INFO_KEY, id)
}
