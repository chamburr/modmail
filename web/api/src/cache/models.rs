use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize)]
pub struct Stats {
    pub version: String,
    pub started: NaiveDateTime,
    pub shards: i32,
    pub guilds: i32,
    pub roles: i32,
    pub channels: i32,
    pub members: i32,
}
#[derive(Debug, Deserialize, Serialize)]
pub struct Status {
    pub shard: i32,
    pub status: String,
    pub session: String,
    pub latency: i32,
    pub last_ack: NaiveDateTime,
}
