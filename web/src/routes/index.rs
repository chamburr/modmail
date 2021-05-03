use crate::{
    auth,
    cache::{self, models::Status, RedisPool},
    constants::STATUS_KEY,
    routes::{ApiResponse, ApiResult},
};

use crate::constants::{GUILDS_KEY, SHARDS_KEY, STARTED_KEY};
use actix_web::{
    get, post,
    web::{Data, Json, Query},
};
use chrono::NaiveDateTime;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Deserialize)]
pub struct Authorization {
    pub code: String,
    pub state: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct Redirect {
    pub uri: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct Stats {
    pub started: NaiveDateTime,
    pub shards: u32,
    pub guilds: u32,
}

#[get("")]
pub async fn index() -> ApiResult<ApiResponse> {
    ApiResponse::ok().finish()
}

#[get("/login")]
pub async fn get_login(
    pool: Data<RedisPool>,
    Query(query): Query<HashMap<String, String>>,
) -> ApiResult<ApiResponse> {
    let uri = query
        .get("redirect")
        .map(|redirect| {
            percent_encoding::percent_decode_str(redirect.as_str())
                .decode_utf8()
                .map(|uri| uri.to_string())
        })
        .transpose()?
        .filter(|redirect| redirect.starts_with('/'));

    let redirect = Redirect {
        uri: Some(auth::get_redirect_uri(&pool, uri).await?),
    };

    ApiResponse::ok().data(redirect).finish()
}

#[post("/authorize")]
pub async fn post_authorize(
    pool: Data<RedisPool>,
    Json(auth): Json<Authorization>,
) -> ApiResult<ApiResponse> {
    let token = auth::token_exchange(&pool, auth.code.as_str())
        .await
        .map_err(|_| ApiResponse::bad_request())?;

    let uri = if let Some(state) = auth.state {
        auth::get_csrf_redirect(&pool, state.as_str()).await?
    } else {
        None
    };

    let redirect = Redirect { uri };
    let cookie = auth::get_token_cookie(token).await?;

    ApiResponse::ok().data(redirect).set_cookie(cookie).finish()
}

#[get("/stats")]
pub async fn get_stats(pool: Data<RedisPool>) -> ApiResult<ApiResponse> {
    let started = cache::get(&pool, STARTED_KEY)
        .await?
        .ok_or_else(ApiResponse::internal_server_error)?;
    let shards = cache::get(&pool, SHARDS_KEY)
        .await?
        .ok_or_else(ApiResponse::internal_server_error)?;
    let guilds = cache::len(&pool, GUILDS_KEY).await?;

    let stats = Stats {
        started,
        shards,
        guilds,
    };

    ApiResponse::ok().data(stats).finish()
}

#[get("/status")]
pub async fn get_status(pool: Data<RedisPool>) -> ApiResult<ApiResponse> {
    let status: Vec<Status> = cache::get(&pool, STATUS_KEY)
        .await?
        .ok_or_else(ApiResponse::internal_server_error)?;

    ApiResponse::ok().data(status).finish()
}
