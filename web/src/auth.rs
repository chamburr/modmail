use crate::{
    cache::{self, RedisPool},
    config::CONFIG,
    constants::{
        csrf_token_key, token_info_key, token_key, CALLBACK_PATH, COOKIE_NAME, CSRF_TOKEN_KEY_TTL,
        TOKEN_INFO_KEY_TTL,
    },
    routes::{ApiError, ApiResponse, ApiResult},
};

use actix_web::{
    cookie::{Cookie, SameSite},
    dev::Payload,
    web::Data,
    FromRequest, HttpMessage, HttpRequest,
};
use chrono::Utc;
use jsonwebtoken::{DecodingKey, EncodingKey, Header, Validation};
use lazy_static::lazy_static;
use oauth2::{
    basic::{BasicClient, BasicTokenResponse},
    reqwest::async_http_client,
    AccessToken, AuthUrl, AuthorizationCode, ClientId, ClientSecret, CsrfToken, RedirectUrl,
    RevocationUrl, Scope, StandardRevocableToken, TokenResponse, TokenUrl,
};
use serde::{Deserialize, Serialize};
use std::{convert::TryInto, future::Future, pin::Pin};
use url::Url;

lazy_static! {
    static ref CLIENT: BasicClient = {
        let client = BasicClient::new(
            ClientId::new(CONFIG.bot_client_id.to_string()),
            Some(ClientSecret::new(CONFIG.bot_client_secret.clone())),
            AuthUrl::new("https://discord.com/api/oauth2/authorize".to_owned()).unwrap(),
            Some(TokenUrl::new("https://discord.com/api/oauth2/token".to_owned()).unwrap()),
        )
        .set_revocation_uri(
            RevocationUrl::new("https://discord.com/api/oauth2/token/revoke".to_owned()).unwrap(),
        );

        let mut redirect_uri = Url::parse(CONFIG.base_uri.as_str()).unwrap();
        redirect_uri.set_path(CALLBACK_PATH);

        client.set_redirect_uri(RedirectUrl::new(redirect_uri.into_string()).unwrap())
    };
}

pub async fn get_csrf_redirect(pool: &RedisPool, token: &str) -> ApiResult<Option<String>> {
    let token: Option<String> = cache::get(pool, csrf_token_key(token)).await?;

    Ok(token)
}

pub async fn get_redirect_uri(pool: &RedisPool, redirect: Option<String>) -> ApiResult<String> {
    let (uri, state) = CLIENT
        .authorize_url(CsrfToken::new_random)
        .add_scope(Scope::new("identify".to_owned()))
        .add_scope(Scope::new("guilds".to_owned()))
        .add_extra_param("prompt", "none")
        .url();

    if let Some(redirect) = redirect {
        cache::set(
            pool,
            csrf_token_key(state.secret()),
            &redirect,
            CSRF_TOKEN_KEY_TTL,
        )
        .await?;
    }

    Ok(uri.to_string())
}

#[derive(Debug, Serialize, Deserialize)]
struct Claims {
    token: String,
    iat: u64,
}

pub async fn token_exchange(pool: &RedisPool, code: &str) -> ApiResult<BasicTokenResponse> {
    let response = CLIENT
        .exchange_code(AuthorizationCode::new(code.to_owned()))
        .request_async(async_http_client)
        .await?;

    if let Some(scopes) = response.scopes() {
        if !scopes.contains(&Scope::new("identify".to_owned()))
            || !scopes.contains(&Scope::new("guilds".to_owned()))
        {
            return Err(ApiResponse::bad_request().into());
        }
    }

    let user = User::from_token(pool, response.access_token().secret()).await?;
    cache::set(
        pool,
        token_key(user.id),
        response.access_token().secret(),
        response.expires_in().unwrap_or_default().as_millis() as usize,
    )
    .await?;

    Ok(response)
}

pub async fn get_token_cookie(exchange: BasicTokenResponse) -> ApiResult<Cookie<'static>> {
    let url = Url::parse(CONFIG.base_uri.as_str())?;
    let domain = url.domain().unwrap_or_default().to_owned();

    let token = jsonwebtoken::encode(
        &Header::default(),
        &Claims {
            token: exchange.access_token().secret().to_owned(),
            iat: Utc::now().timestamp_millis() as u64,
        },
        &EncodingKey::from_base64_secret(CONFIG.api_secret.as_str())?,
    )?;

    let cookie = Cookie::build(COOKIE_NAME, token)
        .domain(domain)
        .http_only(true)
        .max_age(
            exchange.expires_in().unwrap_or_default().try_into().unwrap_or_default()
        )
        .same_site(SameSite::Lax)
        // .secure(true)
        .finish();

    Ok(cookie)
}

#[derive(Debug, Deserialize, Serialize)]
pub struct User {
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub token: String,
    pub id: u64,
    pub username: String,
    pub discriminator: u32,
    pub avatar: String,
}

impl User {
    async fn from_token(pool: &RedisPool, token: &str) -> ApiResult<Self> {
        let user: Option<User> = cache::get(pool, token_info_key(token)).await?;
        if let Some(mut user) = user {
            user.token = token.to_owned();
            return Ok(user);
        }

        let client = twilight_http::Client::new(format!("Bearer {}", token));
        let current_user = client.current_user().await?;

        let mut user = Self {
            token: "".to_owned(),
            id: current_user.id.0,
            username: current_user.name,
            discriminator: current_user.discriminator.parse()?,
            avatar: current_user.avatar.unwrap_or_else(|| "".to_owned()),
        };

        cache::set(pool, token_info_key(token), &user, TOKEN_INFO_KEY_TTL).await?;

        user.token = token.to_owned();
        Ok(user)
    }

    pub async fn revoke_token(self) -> ApiResult<()> {
        CLIENT
            .revoke_token(StandardRevocableToken::AccessToken(AccessToken::new(
                self.token,
            )))
            .unwrap()
            .request_async(async_http_client)
            .await?;

        Ok(())
    }
}

impl FromRequest for User {
    type Error = ApiError;
    type Future = Pin<Box<dyn Future<Output = Result<Self, Self::Error>>>>;
    type Config = ();

    fn from_request(req: &HttpRequest, payload: &mut Payload) -> Self::Future {
        let pool = Data::<RedisPool>::from_request(req, payload).into_inner();
        let cookie: Option<Cookie<'static>> = req.cookie(COOKIE_NAME);

        Box::pin(async move {
            let pool = pool?;

            if let Some(cookie) = cookie {
                if let Ok(token) = jsonwebtoken::decode::<Claims>(
                    cookie.value(),
                    &DecodingKey::from_base64_secret(CONFIG.api_secret.as_str())?,
                    &Validation::default(),
                ) {
                    let user = Self::from_token(&pool, token.claims.token.as_str()).await?;
                    return Ok(user);
                }

                Err(ApiResponse::unauthorized()
                    .message("Your session is invalid, please login again.")
                    .del_cookie(COOKIE_NAME)
                    .into())
            } else {
                Err(ApiResponse::unauthorized().into())
            }
        })
    }
}
