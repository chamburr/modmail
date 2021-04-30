use crate::{
    auth::User,
    cache::RedisPool,
    constants::COOKIE_NAME,
    routes::{ApiResponse, ApiResult},
};

use actix_web::{get, post, web::Data};

#[get("/@me")]
pub async fn get_user_me(user: User, _redis_pool: Data<RedisPool>) -> ApiResult<ApiResponse> {
    ApiResponse::ok().data(user.user).finish()
}

#[post("/@me/logout")]
pub async fn post_user_me_logout(user: User) -> ApiResult<ApiResponse> {
    user.revoke_token().await?;

    ApiResponse::ok().del_cookie(COOKIE_NAME).finish()
}
