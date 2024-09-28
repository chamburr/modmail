use crate::{config::CONFIG, routes::ApiResult};

use actix_web::web::block;
use lazy_static::lazy_static;
use r2d2::{ManageConnection, Pool};
use redis::{AsyncCommands, Client, IntoConnectionInfo, RedisError};
use serde::{de::DeserializeOwned, Serialize};
use tokio::runtime::Runtime;
use url::Url;

pub mod models;

lazy_static! {
    static ref RUNTIME: Runtime = Runtime::new().unwrap();
}

pub struct RedisConnectionManager {
    pub inner: Client,
}

impl RedisConnectionManager {
    pub fn new(info: impl IntoConnectionInfo) -> Result<RedisConnectionManager, RedisError> {
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

pub fn get_pool() -> ApiResult<RedisPool> {
    let mut uri = Url::parse("redis://")?;
    uri.set_host(Some(CONFIG.redis_host.as_str()))?;
    uri.set_port(Some(CONFIG.redis_port))?;

    if !CONFIG.redis_password.is_empty() {
        uri.set_password(Some(CONFIG.redis_password.as_str()))?;
    }

    let pool = Pool::builder().build(RedisConnectionManager::new(uri)?)?;

    Ok(pool)
}

pub async fn get<T: DeserializeOwned>(
    pool: &RedisPool,
    key: impl ToString,
) -> ApiResult<Option<T>> {
    let pool = pool.clone();
    let mut conn = block(move || pool.get()).await?;

    let res: Option<String> = conn.get(key.to_string()).await?;

    Ok(res
        .map(|value| {
            serde_json::from_str(value.as_str())
                .or_else(|_| serde_json::from_str(format!("\"{}\"", value).as_str()))
        })
        .transpose()?)
}

pub async fn set<T: Serialize>(
    pool: &RedisPool,
    key: impl ToString,
    value: &T,
    expiry: usize,
) -> ApiResult<()> {
    let pool = pool.clone();
    let mut conn = block(move || pool.get()).await?;

    let _: () = conn
        .set(
            key.to_string(),
            serde_json::to_string(value)?.trim_matches('"'),
        )
        .await?;

    if expiry != 0 {
        let _: () = conn.expire(key.to_string(), expiry).await?;
    }

    Ok(())
}

pub async fn del(pool: &RedisPool, key: impl ToString) -> ApiResult<()> {
    let pool = pool.clone();
    let mut conn = block(move || pool.get()).await?;

    let _: () = conn.del(key.to_string()).await?;

    Ok(())
}

pub async fn len(pool: &RedisPool, key: impl ToString) -> ApiResult<u32> {
    let pool = pool.clone();
    let mut conn = block(move || pool.get()).await?;

    let res: u32 = conn.scard(key.to_string()).await?;

    Ok(res)
}
