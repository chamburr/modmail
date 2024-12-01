use crate::{
    routes::{ApiResponse, ApiResult},
    CONFIG,
};

use actix_web::{
    get,
    web::{block, Path},
};
use futures::Future;
use lazy_static::lazy_static;
use regex::Regex;
use serde::Serialize;
use std::num::ParseIntError;
use tokio::runtime::Runtime;
use twilight_http::Client;
use twilight_model::id::{ChannelId, MessageId};

lazy_static! {
    static ref CLIENT: Client = Client::new(CONFIG.bot_token.as_str());
    static ref RUNTIME: Runtime = Runtime::new().unwrap();
    static ref RE: Regex =
        Regex::new(r"^\[([0-9-]{10} [0-9:]{8})\] ([^\n]*)#([0-9]{1,4}) \((User|Staff|Comment|Anonymous)\):")
            .unwrap();
}

#[allow(unused)]
async fn block_on<F>(fut: F) -> Result<F::Output, ()>
where
    F: Future + Send + 'static,
    F::Output: Send + Sync,
{
    block(move || -> Result<F::Output, ()> { Ok(RUNTIME.block_on(fut)) })
        .await
        .map_err(|_| ())
}

#[derive(Debug, Serialize)]
pub struct Entry {
    pub timestamp: String,
    pub username: String,
    pub discriminator: String,
    pub role: String,
    pub message: String,
    pub attachments: Vec<String>,
}

#[get("/{id}")]
pub async fn get_log(Path(id): Path<String>) -> ApiResult<ApiResponse> {
    let ids = id
        .split('-')
        .map(|item| u64::from_str_radix(item, 16))
        .collect::<Result<Vec<u64>, ParseIntError>>()
        .map_err(|_| ApiResponse::not_found())?;

    if ids.len() != 3 {
        return ApiResponse::not_found().finish();
    }

    let attachment = block_on(CLIENT.message(ChannelId(ids[0]), MessageId(ids[1])))
        .await?
        .map_err(|_| ApiResponse::not_found())?
        .ok_or_else(ApiResponse::not_found)?
        .attachments
        .into_iter()
        .find(|item| item.id.0 == ids[2])
        .ok_or_else(ApiResponse::not_found)?
        .url;

    let response = block(move || reqwest::blocking::get(attachment)).await?;

    if response.status() != 200 {
        return ApiResponse::not_found().finish();
    }

    let body = block(move || response.text()).await?;
    let mut messages: Vec<Entry> = vec![];

    for line in body.split('\n') {
        if !RE.is_match(line) {
            if let Some(last) = messages.last_mut() {
                last.message += format!("\n{}", line).as_str()
            }
            continue;
        }

        let captures = RE.captures(line).unwrap();
        let timestamp = &captures[1];
        let username = &captures[2];
        let discriminator = &captures[3];
        let role = &captures[4];

        let mut message = line.splitn(2, ": ").last().unwrap_or_default().to_owned();
        if message.starts_with("(Attachment: ") {
            message = format!(" {}", message);
        }

        let mut message_iter = message.splitn(2, "(Attachment: ");
        let message = message_iter.next().unwrap_or_default();
        let attachment = message_iter.next().unwrap_or_default();

        let attachments = attachment
            .split(") (Attachment: ")
            .map(|item| {
                let mut item = item.to_owned();
                if item.ends_with(')') {
                    item.pop();
                }
                item
            })
            .filter(|item| !item.is_empty())
            .collect();

        messages.push(Entry {
            timestamp: timestamp.to_owned(),
            username: username.to_owned(),
            discriminator: discriminator.to_owned(),
            role: role.to_owned(),
            message: message.to_owned(),
            attachments,
        })
    }

    ApiResponse::ok().data(messages).finish()
}
