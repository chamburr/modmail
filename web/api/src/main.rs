#![deny(clippy::all, nonstandard_style, rust_2018_idioms, unused, warnings)]

use crate::config::Environment;
use crate::config::CONFIG;
use crate::routes::errors;

use actix_web::http::StatusCode;
use actix_web::middleware::errhandlers::ErrorHandlers;
use actix_web::middleware::normalize::TrailingSlash;
use actix_web::middleware::{Logger, NormalizePath};
use actix_web::{web, App, HttpServer};
use config::get_api_address;
use dotenv::dotenv;
use routes::ApiResult;
use tracing::error;
use tracing_log::env_logger;

mod config;
mod routes;

#[actix_web::main]
pub async fn main() {
    dotenv().ok();
    tracing_subscriber::fmt::init();
    env_logger::init();

    let result = real_main().await;

    if let Err(err) = result {
        error!("{:?}", err);
    }
}

pub async fn real_main() -> ApiResult<()> {
    let _guard;
    if CONFIG.environment == Environment::Production {
        _guard = sentry::init(CONFIG.sentry_dsn.clone());
    }

    let redis_pool = get_redis_pool()?;

    init_cache(pool.clone(), redis_pool.clone());

    HttpServer::new(move || {
        App::new()
            .data(redis_pool.clone())
            .wrap(
                ErrorHandlers::new()
                    .handler(StatusCode::BAD_REQUEST, errors::bad_request)
                    .handler(StatusCode::UNAUTHORIZED, errors::unauthorized)
                    .handler(StatusCode::FORBIDDEN, errors::forbidden)
                    .handler(StatusCode::NOT_FOUND, errors::not_found)
                    .handler(StatusCode::REQUEST_TIMEOUT, errors::request_timeout)
                    .handler(
                        StatusCode::INTERNAL_SERVER_ERROR,
                        errors::internal_server_error,
                    )
                    .handler(StatusCode::SERVICE_UNAVAILABLE, errors::service_unavailable),
            )
            .wrap(Logger::default())
            .wrap(NormalizePath::new(TrailingSlash::Trim))
            .service(web::scope("/api"))
            .default_service(web::to(errors::default_service))
    })
    .workers(CONFIG.api_workers as usize)
    .bind(get_api_address()?)?
    .run()
    .await?;

    Ok(())
}
