use actix_web::http::StatusCode;
use actix_web::{cookie::Cookie, error::BlockingError};
use actix_web::{HttpMessage, HttpRequest, HttpResponse, Responder, ResponseError};
use futures::future::{ok, Ready};
use http::header::ToStrError;
use redis::RedisError;
use serde::Serialize;
use serde_json::{json, Value};
use std::io;
use std::fmt::{self, Debug, Display, Formatter};
use std::{
    net::AddrParseError,
    num::ParseIntError,
    str::Utf8Error,
};
use twilight_oauth2::client::RedirectUriInvalidError;
use url::ParseError;

pub mod errors;
pub mod index;
pub mod logs;
pub mod users;

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
            if let Some(cookie) = req.cookie(del_cookie.as_str()) {
                res.del_cookie(&cookie);
            }
        }

        ok(res.json(self.data))
    }
}

#[derive(Debug)]
pub enum ApiError {
    ActixWebError(()),
    AddrParseError(AddrParseError),
    CustomError((StatusCode, Value)),
    EmptyError(()),
    IoError(io::Error),
    JsonWebTokenError(jsonwebtoken::errors::Error),
    ParseError(ParseError),
    ParseIntError(ParseIntError),
    R2d2Error(r2d2::Error),
    RedirectUriInvalidError(RedirectUriInvalidError<'static>),
    RedisError(RedisError),
    RegexError(regex::Error),
    ReqwestError(reqwest::Error),
    SerdeJsonError(serde_json::Error),
    ToStrError(ToStrError),
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

impl From<AddrParseError> for ApiError {
    fn from(err: AddrParseError) -> Self {
        sentry::capture_error(&err);
        Self::AddrParseError(err)
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

impl From<ApiResponse> for ApiError {
    fn from(err: ApiResponse) -> Self {
        Self::CustomError((err.status, err.data))
    }
}

impl From<()> for ApiError {
    fn from(_: ()) -> Self {
        Self::EmptyError(())
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

impl From<RedirectUriInvalidError<'_>> for ApiError {
    fn from(err: RedirectUriInvalidError<'_>) -> Self {
        sentry::capture_error(&err);
        match err {
            RedirectUriInvalidError::Invalid { source, .. } => {
                Self::RedirectUriInvalidError(RedirectUriInvalidError::Invalid { source, uri: "" })
            }
            RedirectUriInvalidError::Unconfigured { uri } => {
                Self::RedirectUriInvalidError(RedirectUriInvalidError::Unconfigured { uri })
            }
            _ => Self::EmptyError(()),
        }
    }
}

impl From<RedisError> for ApiError {
    fn from(err: RedisError) -> Self {
        sentry::capture_error(&err);
        Self::RedisError(err)
    }
}

impl From<regex::Error> for ApiError {
    fn from(err: regex::Error) -> Self {
        sentry::capture_error(&err);
        Self::RegexError(err)
    }
}

impl From<reqwest::Error> for ApiError {
    fn from(err: reqwest::Error) -> Self {
        sentry::capture_error(&err);
        Self::ReqwestError(err)
    }
}

impl From<serde_json::Error> for ApiError {
    fn from(err: serde_json::Error) -> Self {
        sentry::capture_error(&err);
        Self::SerdeJsonError(err)
    }
}

impl From<ToStrError> for ApiError {
    fn from(err: ToStrError) -> Self {
        sentry::capture_error(&err);
        Self::ToStrError(err)
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

pub trait OptionExt<T> {
    fn or_bad_request(self) -> ApiResult<T>;
    fn or_not_found(self) -> ApiResult<T>;
    fn or_internal_error(self) -> ApiResult<T>;
}

impl<T> OptionExt<T> for Option<T> {
    fn or_bad_request(self) -> ApiResult<T> {
        self.ok_or_else(|| ApiResponse::bad_request().into())
    }

    fn or_not_found(self) -> ApiResult<T> {
        self.ok_or_else(|| ApiResponse::not_found().into())
    }

    fn or_internal_error(self) -> ApiResult<T> {
        self.ok_or_else(|| ApiResponse::internal_server_error().into())
    }
}

pub trait ResultExt<T, E> {
    fn or_bad_request(self) -> ApiResult<T>;
    fn or_not_found(self) -> ApiResult<T>;
    fn or_internal_error(self) -> ApiResult<T>;
}

impl<T, E> ResultExt<T, E> for Result<T, E> {
    fn or_bad_request(self) -> ApiResult<T> {
        self.map_err(|_| ApiResponse::bad_request().into())
    }

    fn or_not_found(self) -> ApiResult<T> {
        self.map_err(|_| ApiResponse::not_found().into())
    }

    fn or_internal_error(self) -> ApiResult<T> {
        self.map_err(|_| ApiResponse::internal_server_error().into())
    }
}
