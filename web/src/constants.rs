pub const COOKIE_NAME: &str = "session";
pub const CALLBACK_PATH: &str = "/callback";

pub const CSRF_TOKEN_KEY: &str = "csrf_token";
pub const SHARDS_KEY: &str = "gateway_shards";
pub const STARTED_KEY: &str = "gateway_started";
pub const STATUS_KEY: &str = "gateway_statuses";
pub const GUILDS_KEY: &str = "guild_keys";
pub const TOKEN_KEY: &str = "token";
pub const USER_TOKEN_KEY: &str = "user_token";

pub const CSRF_TOKEN_KEY_TTL: usize = 300;
pub const TOKEN_KEY_TTL: usize = 60;

pub fn csrf_token_key(id: &str) -> String {
    format!("{}:{}", CSRF_TOKEN_KEY, id)
}

pub fn token_key(id: &str) -> String {
    format!("{}:{}", TOKEN_KEY, id)
}

pub fn user_token_key(id: &str) -> String {
    format!("{}:{}", USER_TOKEN_KEY, id)
}
