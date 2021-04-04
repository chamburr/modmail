use crate::constants::COOKIE_NAME;
use crate::cache::RedisPool;
use crate::routes::{ApiResponse, ApiResult};
use crate::auth::User;

use actix_web::web::Data;
use actix_web::{get, post};

#[get("/@me")]
pub async fn get_user_me(user: User, _redis_pool: Data<RedisPool>) -> ApiResult<ApiResponse> {
    ApiResponse::ok().data(user.user).finish()
}

#[get("/@me/guilds")]
pub async fn get_user_me_guilds(user: User, redis_pool: Data<RedisPool>) -> ApiResult<ApiResponse> {
    let guilds = user.get_guilds(&redis_pool).await?;

    ApiResponse::ok().data(guilds).finish()
}

#[post("/@me/logout")]
pub async fn post_user_me_logout(user: User) -> ApiResult<ApiResponse> {
    user.revoke_token().await?;

    ApiResponse::ok().del_cookie(COOKIE_NAME).finish()
}
