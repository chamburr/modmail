#![deny(clippy::all, nonstandard_style, rust_2018_idioms, unused, warnings)]

use crate::{
    config::CONFIG,
    routes::{errors, index, logs, users, webhooks, ApiResult},
};

use actix_web::{
    http::StatusCode,
    middleware::{errhandlers::ErrorHandlers, normalize::TrailingSlash, Logger, NormalizePath},
    web, App, HttpServer,
};

mod auth;
mod cache;
mod config;
mod constants;
mod routes;

#[actix_web::main]
pub async fn main() {
    dotenv::from_filename("../.env").ok();

    if std::env::var("RUST_LOG").is_err() {
        std::env::set_var("RUST_LOG", "info");
    }

    tracing_subscriber::fmt::init();
    tracing_log::env_logger::init();

    let result = real_main().await;

    if let Err(err) = result {
        tracing::error!("{:?}", err);
    }
}

pub async fn real_main() -> ApiResult<()> {
    std::env::set_var("RUST_BACKTRACE", "1");

    let pool = cache::get_pool()?;

    HttpServer::new(move || {
        App::new()
            .data(pool.clone())
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
            .service(
                web::scope("/api")
                    .service(index::index)
                    .service(index::get_login)
                    .service(index::get_stats)
                    .service(index::get_status)
                    .service(index::post_authorize)
                    .service(
                        web::scope("/users")
                            .service(users::get_user_me)
                            .service(users::post_user_me_logout),
                    )
                    .service(web::scope("/logs").service(logs::get_log))
                    .service(web::scope("/webhooks").service(webhooks::post_payment)),
            )
            .default_service(web::to(errors::default_service))
    })
    .workers(CONFIG.api_workers as usize)
    .bind((CONFIG.api_host.as_str(), CONFIG.api_port))?
    .run()
    .await?;

    Ok(())
}
