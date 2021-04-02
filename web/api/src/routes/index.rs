use crate::constants::{PLAYER_STATS_KEY, STATS_KEY, STATUS_KEY};
use crate::db::cache::models::{Stats, Status};
use crate::db::{cache, RedisPool};
use crate::routes::{ApiResponse, ApiResult, OptionExt, ResultExt};
use crate::auth::{
    get_csrf_redirect, get_invite_uri, get_redirect_uri, get_token_cookie, token_exchange,
};

use actix_web::web::{Data, Json, Query};
use actix_web::{get, post};
use percent_encoding::percent_decode_str;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Serialize)]
pub struct SimpleRedirect {
    pub uri: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct SimpleAuth {
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
            percent_decode_str(redirect.as_str())
                .decode_utf8()
                .map(|uri| uri.to_string())
        })
        .transpose()?
        .filter(|redirect| redirect.starts_with('/'));

    let redirect = SimpleRedirect {
        uri: Some(get_redirect_uri(&redis_pool, uri).await?),
    };

    ApiResponse::ok().data(redirect).finish()
}

#[get("/invite")]
pub async fn get_invite(Query(query): Query<HashMap<String, String>>) -> ApiResult<ApiResponse> {
    let guild = query
        .get("guild")
        .map(|guild| guild.parse().or_bad_request())
        .transpose()?;

    let redirect = SimpleRedirect {
        uri: Some(get_invite_uri(guild)?),
    };

    ApiResponse::ok().data(redirect).finish()
}

#[post("/authorize")]
pub async fn get_authorize(
    redis_pool: Data<RedisPool>,
    Json(auth): Json<SimpleAuth>,
) -> ApiResult<ApiResponse> {
    let token = token_exchange(auth.code.as_str()).await.or_bad_request()?;

    let uri = if let Some(state) = auth.state {
        get_csrf_redirect(&redis_pool, state.as_str()).await?
    } else {
        None
    };

    let redirect = SimpleRedirect { uri };
    let cookie = get_token_cookie(token).await?;

    ApiResponse::ok().data(redirect).set_cookie(cookie).finish()
}

#[get("/stats")]
pub async fn get_stats(redis_pool: Data<RedisPool>) -> ApiResult<ApiResponse> {
    let stats: Stats = cache::get(&redis_pool, STATS_KEY)
        .await?
        .or_internal_error()?;

    ApiResponse::ok().data(stats).finish()
}

#[get("/stats/player")]
pub async fn get_stats_player(redis_pool: Data<RedisPool>) -> ApiResult<ApiResponse> {
    let stats: twilight_andesite::model::Stats = cache::get(&redis_pool, PLAYER_STATS_KEY)
        .await?
        .or_internal_error()?;

    ApiResponse::ok().data(stats).finish()
}

#[get("/status")]
pub async fn get_status(redis_pool: Data<RedisPool>) -> ApiResult<ApiResponse> {
    let status: Vec<Status> = cache::get(&redis_pool, STATUS_KEY)
        .await?
        .or_internal_error()?;

    ApiResponse::ok().data(status).finish()
}
