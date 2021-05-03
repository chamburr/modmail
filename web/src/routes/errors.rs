use crate::routes::{ApiResponse, ApiResult};

use actix_web::{
    body::{Body, BodySize, MessageBody, ResponseBody},
    dev::ServiceResponse,
    http::{header::CONTENT_TYPE, HeaderValue},
    middleware::errhandlers::ErrorHandlerResponse,
    Result,
};

fn respond_error<B: MessageBody>(
    res: ServiceResponse<B>,
    response: ApiResponse,
) -> ErrorHandlerResponse<B> {
    let res = res.map_body(|header, body| match body.size() {
        BodySize::Sized(_) => body,
        _ => {
            header.headers_mut().insert(
                CONTENT_TYPE,
                HeaderValue::from_str("application/json").unwrap(),
            );
            ResponseBody::Body(Body::from(response.data)).into_body()
        }
    });

    ErrorHandlerResponse::Response(res)
}

pub fn bad_request<B: MessageBody>(res: ServiceResponse<B>) -> Result<ErrorHandlerResponse<B>> {
    Ok(respond_error(res, ApiResponse::bad_request()))
}

pub fn unauthorized<B: MessageBody>(res: ServiceResponse<B>) -> Result<ErrorHandlerResponse<B>> {
    Ok(respond_error(res, ApiResponse::unauthorized()))
}

pub fn forbidden<B: MessageBody>(res: ServiceResponse<B>) -> Result<ErrorHandlerResponse<B>> {
    Ok(respond_error(res, ApiResponse::forbidden()))
}

pub fn not_found<B: MessageBody>(res: ServiceResponse<B>) -> Result<ErrorHandlerResponse<B>> {
    Ok(respond_error(res, ApiResponse::not_found()))
}

pub fn request_timeout<B: MessageBody>(res: ServiceResponse<B>) -> Result<ErrorHandlerResponse<B>> {
    Ok(respond_error(res, ApiResponse::request_timeout()))
}

pub fn internal_server_error<B: MessageBody>(
    res: ServiceResponse<B>,
) -> Result<ErrorHandlerResponse<B>> {
    Ok(respond_error(res, ApiResponse::internal_server_error()))
}

pub fn service_unavailable<B: MessageBody>(
    res: ServiceResponse<B>,
) -> Result<ErrorHandlerResponse<B>> {
    Ok(respond_error(res, ApiResponse::service_unavailable()))
}

pub async fn default_service() -> ApiResult<ApiResponse> {
    ApiResponse::not_found().finish()
}
