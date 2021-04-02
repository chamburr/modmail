use crate::{cache::RedisPool, constants::BLACKLIST_KEY};
use crate::routes::ApiResult;

use actix_web::web::block;
use redis::AsyncCommands;
use serde::Serialize;
use serde::de::DeserializeOwned;

pub async fn get<T: DeserializeOwned>(
    pool: &RedisPool,
    key: impl ToString,
) -> ApiResult<Option<T>> {
    let pool = pool.clone();
    let mut conn = block(move || pool.get()).await?;
    let res: Option<String> = conn.get(key.to_string()).await?;

    let res: Option<T> = res
        .map(|value| serde_json::from_str(value.as_str()))
        .transpose()?;

    Ok(res)
}

pub async fn set<T: Serialize>(pool: &RedisPool, key: impl ToString, value: &T) -> ApiResult<()> {
    let pool = pool.clone();
    let mut conn = block(move || pool.get()).await?;
    conn.set(key.to_string(), serde_json::to_string(value)?)
        .await?;

    Ok(())
}

pub async fn set_and_expire<T: Serialize>(
    pool: &RedisPool,
    key: impl ToString,
    value: &T,
    expiry: usize,
) -> ApiResult<()> {
    set(pool, key.to_string(), value).await?;

    let pool = pool.clone();
    let mut conn = block(move || pool.get()).await?;
    conn.expire(key.to_string(), expiry / 1000).await?;

    Ok(())
}

pub async fn sismember(
    pool: &RedisPool,
    key: impl ToString,
    value: impl ToString,
) -> ApiResult<bool> {
    let pool = pool.clone();
    let mut conn = block(move || pool.get()).await?;
    let res = conn.sismember(key.to_string(), value.to_string()).await?;

    Ok(res)
}

pub async fn get_blacklist_item(pool: &RedisPool, user: u64) -> ApiResult<Option<()>> {
    let blacklist = sismember(pool, BLACKLIST_KEY, &user).await?;

    if blacklist {
        Ok(Some(()))
    } else {
        Ok(None)
    }
}
