use crate::{config::get_redis_uri, routes::ApiResult};

use lazy_static::lazy_static;
use r2d2::{ManageConnection, Pool};
use redis::{Client, IntoConnectionInfo, RedisError};
use tokio::runtime::Runtime;

pub mod commands;
pub mod models;

lazy_static! {
    static ref RUNTIME: Runtime = Runtime::new().unwrap();
}

pub struct RedisConnectionManager {
    pub inner: Client,
}

impl RedisConnectionManager {
    pub fn new(info: String) -> Result<RedisConnectionManager, RedisError> {
        Ok(RedisConnectionManager {
            inner: Client::open(info.into_connection_info()?)?,
        })
    }
}

impl ManageConnection for RedisConnectionManager {
    type Connection = redis::aio::Connection;
    type Error = RedisError;

    fn connect(&self) -> Result<Self::Connection, Self::Error> {
        RUNTIME.block_on(async move { self.inner.get_async_connection().await })
    }

    fn is_valid(&self, conn: &mut Self::Connection) -> Result<(), Self::Error> {
        RUNTIME.block_on(async move { redis::cmd("PING").query_async(conn).await })
    }

    fn has_broken(&self, _: &mut Self::Connection) -> bool {
        false
    }
}

pub type RedisPool = Pool<RedisConnectionManager>;

pub fn get_redis_pool() -> ApiResult<RedisPool> {
    let uri = get_redis_uri()?;
    let pool = Pool::builder().build(RedisConnectionManager::new(uri)?)?;

    Ok(pool)
}
