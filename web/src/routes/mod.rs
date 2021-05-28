use crate::config::CONFIG;

use actix_web::{
    cookie::Cookie, error::BlockingError, http::StatusCode, HttpMessage, HttpRequest, HttpResponse,
    Responder, ResponseError,
};
use futures::future::{ok, Ready};
use oauth2::{
    basic::BasicErrorResponseType, RequestTokenError, RevocationErrorResponseType,
    StandardErrorResponse,
};
use redis::RedisError;
use serde::Serialize;
use serde_json::{json, Value};
use std::{
    fmt::{self, Debug, Display, Formatter},
    io,
    num::ParseIntError,
    str::Utf8Error,
    string::FromUtf8Error,
};
use twilight_embed_builder::EmbedError;
use twilight_http::request::channel::message::create_message::CreateMessageError;
use url::{ParseError, Url};

pub mod errors;
pub mod index;
pub mod logs;
pub mod users;
pub mod webhooks;

pub type ApiResult<T> = Result<T, ApiError>;

#[derive(Debug)]
pub struct ApiResponse {
    pub status: StatusCode,
    pub data: Value,
    pub error: Option<ApiError>,
    pub set_cookie: Option<Cookie<'static>>,
    pub del_cookie: Option<String>,
}

impl ApiResponse {
    pub fn finish(self) -> ApiResult<Self> {
        match self.error {
            Some(err) => Err(err),
            None => match self.status {
                StatusCode::OK => Ok(self),
                _ => Err(self.into()),
            },
        }
    }

    pub fn data(mut self, data: impl Serialize) -> Self {
        match serde_json::to_value(data) {
            Ok(value) => self.data = value,
            Err(err) => self.error = Some(err.into()),
        }
        self
    }

    pub fn message(mut self, message: &str) -> Self {
        self.data = json!({ "message": message });
        self
    }

    pub fn set_cookie(mut self, set_cookie: Cookie<'static>) -> Self {
        self.set_cookie = Some(set_cookie);
        self
    }

    pub fn del_cookie(mut self, del_cookie: &str) -> Self {
        self.del_cookie = Some(del_cookie.to_owned());
        self
    }

    pub fn ok() -> Self {
        Self {
            status: StatusCode::OK,
            data: json!({"message": "The request made is successful."}),
            error: None,
            set_cookie: None,
            del_cookie: None,
        }
    }

    pub fn bad_request() -> Self {
        Self {
            status: StatusCode::BAD_REQUEST,
            data: json!({"message": "The request you made is invalid."}),
            error: None,
            set_cookie: None,
            del_cookie: None,
        }
    }

    pub fn unauthorized() -> Self {
        Self {
            status: StatusCode::UNAUTHORIZED,
            data: json!({"message": "You are not authorised to access this resource."}),
            error: None,
            set_cookie: None,
            del_cookie: None,
        }
    }

    pub fn forbidden() -> Self {
        Self {
            status: StatusCode::FORBIDDEN,
            data: json!({"message": "You do not have permission to perform this action."}),
            error: None,
            set_cookie: None,
            del_cookie: None,
        }
    }

    pub fn not_found() -> Self {
        Self {
            status: StatusCode::NOT_FOUND,
            data: json!({"message": "The requested resource could not be found."}),
            error: None,
            set_cookie: None,
            del_cookie: None,
        }
    }

    pub fn request_timeout() -> Self {
        Self {
            status: StatusCode::REQUEST_TIMEOUT,
            data: json!({"message": "The server did not receive a complete request."}),
            error: None,
            set_cookie: None,
            del_cookie: None,
        }
    }

    pub fn internal_server_error() -> Self {
        Self {
            status: StatusCode::INTERNAL_SERVER_ERROR,
            data: json!({"message": "The server encountered an internal error."}),
            error: None,
            set_cookie: None,
            del_cookie: None,
        }
    }

    pub fn service_unavailable() -> Self {
        Self {
            status: StatusCode::SERVICE_UNAVAILABLE,
            data: json!({"message": "The server cannot handle your request at this time."}),
            error: None,
            set_cookie: None,
            del_cookie: None,
        }
    }
}

impl Responder for ApiResponse {
    type Error = actix_web::Error;
    type Future = Ready<Result<HttpResponse, actix_web::Error>>;

    fn respond_to(self, req: &HttpRequest) -> Self::Future {
        let mut res = HttpResponse::build(self.status);

        if let Some(set_cookie) = self.set_cookie {
            res.cookie(set_cookie);
        }

        if let Some(del_cookie) = self.del_cookie {
            if let Some(mut cookie) = req.cookie(del_cookie.as_str()) {
                let url = Url::parse(CONFIG.base_uri.as_str()).unwrap();
                let domain = url.domain().unwrap_or_default();

                cookie.set_path("/");
                cookie.set_domain(domain);

                res.del_cookie(&cookie);
            }
        }

        ok(res.json(self.data))
    }
}

#[derive(Debug)]
pub enum ApiError {
    ActixWebError(()),
    CreateMessageError(CreateMessageError),
    CustomError((StatusCode, Value)),
    EmbedError(EmbedError),
    EmptyError(()),
    FromUtf8Error(FromUtf8Error),
    IoError(io::Error),
    JsonWebTokenError(jsonwebtoken::errors::Error),
    ParseError(ParseError),
    ParseIntError(ParseIntError),
    R2d2Error(r2d2::Error),
    RedisError(RedisError),
    RequestTokenErrorBasic(
        RequestTokenError<
            oauth2::reqwest::Error<reqwest::Error>,
            StandardErrorResponse<BasicErrorResponseType>,
        >,
    ),
    RequestTokenErrorRevocation(
        RequestTokenError<
            oauth2::reqwest::Error<reqwest::Error>,
            StandardErrorResponse<RevocationErrorResponseType>,
        >,
    ),
    ReqwestError(reqwest::Error),
    SerdeJsonError(serde_json::Error),
    SerdeUrlEncodedError(serde_urlencoded::de::Error),
    TwilightHttpError(twilight_http::Error),
    Utf8Error(Utf8Error),
}

impl Display for ApiError {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        write!(f, "{:?}", self)
    }
}

impl ResponseError for ApiError {
    fn error_response(&self) -> HttpResponse {
        match self {
            Self::CustomError((status, value)) => HttpResponse::build(*status).json(value),
            _ => {
                let res = ApiResponse::internal_server_error();
                HttpResponse::build(res.status).json(&res.data)
            }
        }
    }
}

impl From<actix_web::Error> for ApiError {
    fn from(err: actix_web::Error) -> Self {
        sentry::capture_error(&err);
        Self::ActixWebError(())
    }
}

impl From<BlockingError<r2d2::Error>> for ApiError {
    fn from(err: BlockingError<r2d2::Error>) -> Self {
        sentry::capture_error(&err);
        match err {
            BlockingError::Error(error) => Self::R2d2Error(error),
            BlockingError::Canceled => Self::EmptyError(()),
        }
    }
}

impl
    From<
        BlockingError<
            RequestTokenError<
                oauth2::reqwest::Error<reqwest::Error>,
                StandardErrorResponse<BasicErrorResponseType>,
            >,
        >,
    > for ApiError
{
    fn from(
        err: BlockingError<
            RequestTokenError<
                oauth2::reqwest::Error<reqwest::Error>,
                StandardErrorResponse<BasicErrorResponseType>,
            >,
        >,
    ) -> Self {
        sentry::capture_error(&err);
        match err {
            BlockingError::Error(error) => Self::RequestTokenErrorBasic(error),
            BlockingError::Canceled => Self::EmptyError(()),
        }
    }
}

impl
    From<
        BlockingError<
            RequestTokenError<
                oauth2::reqwest::Error<reqwest::Error>,
                StandardErrorResponse<RevocationErrorResponseType>,
            >,
        >,
    > for ApiError
{
    fn from(
        err: BlockingError<
            RequestTokenError<
                oauth2::reqwest::Error<reqwest::Error>,
                StandardErrorResponse<RevocationErrorResponseType>,
            >,
        >,
    ) -> Self {
        sentry::capture_error(&err);
        match err {
            BlockingError::Error(error) => Self::RequestTokenErrorRevocation(error),
            BlockingError::Canceled => Self::EmptyError(()),
        }
    }
}

impl From<BlockingError<reqwest::Error>> for ApiError {
    fn from(err: BlockingError<reqwest::Error>) -> Self {
        sentry::capture_error(&err);
        match err {
            BlockingError::Error(error) => Self::ReqwestError(error),
            BlockingError::Canceled => Self::EmptyError(()),
        }
    }
}

impl From<CreateMessageError> for ApiError {
    fn from(err: CreateMessageError) -> Self {
        sentry::capture_error(&err);
        Self::CreateMessageError(err)
    }
}

impl From<ApiResponse> for ApiError {
    fn from(err: ApiResponse) -> Self {
        Self::CustomError((err.status, err.data))
    }
}

impl From<FromUtf8Error> for ApiError {
    fn from(err: FromUtf8Error) -> Self {
        sentry::capture_error(&err);
        Self::FromUtf8Error(err)
    }
}

impl From<()> for ApiError {
    fn from(_: ()) -> Self {
        Self::EmptyError(())
    }
}

impl From<EmbedError> for ApiError {
    fn from(err: EmbedError) -> Self {
        sentry::capture_error(&err);
        Self::EmbedError(err)
    }
}

impl From<io::Error> for ApiError {
    fn from(err: io::Error) -> Self {
        sentry::capture_error(&err);
        Self::IoError(err)
    }
}

impl From<jsonwebtoken::errors::Error> for ApiError {
    fn from(err: jsonwebtoken::errors::Error) -> Self {
        sentry::capture_error(&err);
        Self::JsonWebTokenError(err)
    }
}

impl From<ParseError> for ApiError {
    fn from(err: ParseError) -> Self {
        sentry::capture_error(&err);
        Self::ParseError(err)
    }
}

impl From<ParseIntError> for ApiError {
    fn from(err: ParseIntError) -> Self {
        sentry::capture_error(&err);
        Self::ParseIntError(err)
    }
}

impl From<r2d2::Error> for ApiError {
    fn from(err: r2d2::Error) -> Self {
        sentry::capture_error(&err);
        Self::R2d2Error(err)
    }
}

impl From<RedisError> for ApiError {
    fn from(err: RedisError) -> Self {
        sentry::capture_error(&err);
        Self::RedisError(err)
    }
}

impl From<serde_json::Error> for ApiError {
    fn from(err: serde_json::Error) -> Self {
        sentry::capture_error(&err);
        Self::SerdeJsonError(err)
    }
}

impl From<serde_urlencoded::de::Error> for ApiError {
    fn from(err: serde_urlencoded::de::Error) -> Self {
        sentry::capture_error(&err);
        Self::SerdeUrlEncodedError(err)
    }
}

impl From<twilight_http::Error> for ApiError {
    fn from(err: twilight_http::Error) -> Self {
        sentry::capture_error(&err);
        Self::TwilightHttpError(err)
    }
}

impl From<Utf8Error> for ApiError {
    fn from(err: Utf8Error) -> Self {
        sentry::capture_error(&err);
        Self::Utf8Error(err)
    }
}
