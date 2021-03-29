use crate::routes::{ApiResponse, ApiResult};

use actix_web::body::Body;
use actix_web::dev::ServiceResponse;
use actix_web::middleware::errhandlers::ErrorHandlerResponse;
use actix_web::web::HttpResponse;
use actix_web::Result;

fn respond_error<B>(res: ServiceResponse<B>, response: ApiResponse) -> ErrorHandlerResponse<Body> {
    let response = HttpResponse::build(response.status).json(response.data);

    ErrorHandlerResponse::Response(res.into_response(response))
}

pub fn bad_request<B>(res: ServiceResponse<B>) -> Result<ErrorHandlerResponse<Body>> {
    Ok(respond_error(res, ApiResponse::bad_request()))
}

pub fn unauthorized<B>(res: ServiceResponse<B>) -> Result<ErrorHandlerResponse<Body>> {
    Ok(respond_error(res, ApiResponse::bad_request()))
}

pub fn forbidden<B>(res: ServiceResponse<B>) -> Result<ErrorHandlerResponse<Body>> {
    Ok(respond_error(res, ApiResponse::forbidden()))
}

pub fn not_found<B>(res: ServiceResponse<B>) -> Result<ErrorHandlerResponse<Body>> {
    Ok(respond_error(res, ApiResponse::not_found()))
}

pub fn request_timeout<B>(res: ServiceResponse<B>) -> Result<ErrorHandlerResponse<Body>> {
    Ok(respond_error(res, ApiResponse::request_timeout()))
}

pub fn internal_server_error<B>(res: ServiceResponse<B>) -> Result<ErrorHandlerResponse<Body>> {
    Ok(respond_error(res, ApiResponse::internal_server_error()))
}

pub fn service_unavailable<B>(res: ServiceResponse<B>) -> Result<ErrorHandlerResponse<Body>> {
    Ok(respond_error(res, ApiResponse::service_unavailable()))
}

pub async fn default_service() -> ApiResult<ApiResponse> {
    ApiResponse::not_found().finish()
}
