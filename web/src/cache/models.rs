use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize, Serialize)]
pub struct Status {
    pub shard: i32,
    pub status: String,
    pub latency: i32,
    pub last_ack: NaiveDateTime,
}
