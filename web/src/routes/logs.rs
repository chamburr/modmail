use crate::routes::{ApiResponse, ApiResult, ResultExt};

use actix_web::get;
use regex::Regex;
use serde::Serialize;

#[derive(Debug, Serialize)]
pub struct MsgEntry {
    pub timestamp: String,
    pub username: String,
    pub discriminator: String,
    pub role: String,
    pub message: String,
    pub attachments: Vec<String>,
}

#[get("/{item}")]
pub async fn get_log_item(item: String) -> ApiResult<ApiResponse> {
    let ids: Vec<&str> = item.split('-').collect();

    if ids.len() != 3 {
        return ApiResponse::not_found().finish();
    }

    let mut new_ids = vec![];

    for id in ids {
        new_ids.push(u64::from_str_radix(id, 16).or_not_found()?);
    }

    let response = reqwest::get(
        format!(
            "https://cdn.discordapp.com/attachments/{}/{}/modmail_log_{}.txt",
            new_ids[0], new_ids[2], new_ids[3]
        )
        .as_str(),
    )
    .await?;

    if response.status().as_str() != "200" {
        return ApiResponse::not_found().finish();
    }

    let body = response.text().await?;
    let mut messages: Vec<MsgEntry> = vec![];
    let re = Regex::new(r"^\[[0-9-]{10} [0-9:]{8}\] [^\n]*#[0-9]{4} \((User|Staff|Comment)\):")?;

    for line in body.split('\n') {
        if !re.is_match(line) {
            let i = messages.len();

            if i > 0 {
                messages[i - 1].message += format!("\n{}", line).as_str();
            }

            continue;
        }

        let new_line: Vec<&str> = line.split('#').collect();
        let part_one = new_line[0];
        let part_two = &new_line[1..].join("#");
        let timestamp = part_one[1..20].to_string();
        let username = part_one[22..].to_string();
        let discriminator = part_two[..4].to_string();

        let mut role = "User".to_string();

        if part_two[6..].starts_with("Staff") {
            role = "Staff".to_string();
        } else if part_two[6..].starts_with("Comment") {
            role = "Comment".to_string();
        }

        let mut message = part_two.split(": ").collect::<Vec<&str>>()[1..].join(": ");

        if message.starts_with("(Attachment: ") {
            message = format!(" {}", message);
        }

        let attachment =
            message.split("(Attachment: ").collect::<Vec<&str>>()[1..].join(" (Attachment: ");
        message = message.split(" (Attachment: ").collect::<Vec<&str>>()[0].to_string();

        let mut attachments: Vec<String> = vec![];

        for mut element in attachment.split(") (Attachment: ") {
            if element.ends_with(')') {
                element = &element[..element.len() - 1];
            }

            if element.is_empty() {
                attachments.push(element.to_string());
            }
        }

        messages.push(MsgEntry {
            timestamp,
            username,
            discriminator,
            role,
            message,
            attachments,
        })
    }

    ApiResponse::ok().data(messages).finish()
}
