use crate::{
    auth,
    cache::{
        self,
        models::{Stats, Status},
        RedisPool,
    },
    constants::{STATS_KEY, STATUS_KEY},
    routes::{ApiResponse, ApiResult},
};

use actix_web::{
    get, post,
    web::{Data, Json, Query},
};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Serialize)]
pub struct Redirect {
    pub uri: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct Authorization {
    pub code: String,
    pub state: Option<String>,
}

#[get("")]
pub async fn index() -> ApiResult<ApiResponse> {
    ApiResponse::ok().finish()
}

#[get("/login")]
pub async fn get_login(
    redis_pool: Data<RedisPool>,
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
        uri: Some(auth::get_redirect_uri(&redis_pool, uri).await?),
    };

    ApiResponse::ok().data(redirect).finish()
}

#[post("/authorize")]
pub async fn post_authorize(
    redis_pool: Data<RedisPool>,
    Json(auth): Json<Authorization>,
) -> ApiResult<ApiResponse> {
    let token = auth::token_exchange(&redis_pool, auth.code.as_str())
        .await
        .map_err(|_| ApiResponse::bad_request())?;

    let uri = if let Some(state) = auth.state {
        auth::get_csrf_redirect(&redis_pool, state.as_str()).await?
    } else {
        None
    };

    let redirect = Redirect { uri };
    let cookie = auth::get_token_cookie(token).await?;

    ApiResponse::ok().data(redirect).set_cookie(cookie).finish()
}

#[get("/stats")]
pub async fn get_stats(redis_pool: Data<RedisPool>) -> ApiResult<ApiResponse> {
    let stats: Stats = cache::get(&redis_pool, STATS_KEY)
        .await?
        .ok_or_else(ApiResponse::internal_server_error)?;

    ApiResponse::ok().data(stats).finish()
}

#[get("/status")]
pub async fn get_status(redis_pool: Data<RedisPool>) -> ApiResult<ApiResponse> {
    let status: Vec<Status> = cache::get(&redis_pool, STATUS_KEY)
        .await?
        .ok_or_else(ApiResponse::internal_server_error)?;

    ApiResponse::ok().data(status).finish()
}
