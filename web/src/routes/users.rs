use crate::{
    auth::User,
    cache::{self, RedisPool},
    constants::{token_key, user_token_key, COOKIE_NAME},
    routes::{ApiResponse, ApiResult},
};

use actix_web::{get, post, web::Data};

#[get("/@me")]
pub async fn get_user_me(mut user: User, _pool: Data<RedisPool>) -> ApiResult<ApiResponse> {
    user.token.clear();

    ApiResponse::ok().data(user).finish()
}

#[post("/@me/logout")]
pub async fn post_user_me_logout(user: User, pool: Data<RedisPool>) -> ApiResult<ApiResponse> {
    user.revoke_token().await?;
    cache::del(&pool, user_token_key(user.id.as_str())).await?;
    cache::del(&pool, token_key(user.token.as_str())).await?;

    ApiResponse::ok().del_cookie(COOKIE_NAME).finish()
}
