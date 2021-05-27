use crate::CONFIG;

use actix_web::post;
use actix_web::web::{block, Form};
use serde::Deserialize;
use twilight_embed_builder::{EmbedBuilder, EmbedFieldBuilder};
use twilight_http::Client;

#[derive(Debug, Deserialize)]
pub struct PaymentEvent {
    pub custom: String,
    pub first_name: String,
    pub item_name: String,
    pub last_name: String,
    pub mc_gross: String,
    pub mc_currency: String,
    pub payer_email: String,
    pub payment_status: String,
    pub receiver_email: String,
}

#[post("/payment")]
pub async fn post_webhook_payment(bytes: Bytes, Form(payment_event): Form<PaymentEvent>) {
    ApiResponse::ok().finish();

    let query = format!(
        "cmd=_notify-validate&{}",
        String::from_utf8(bytes.to_vec())?
    );

    let validity = block(move || {
        reqwest::blocking::post(format!("https://ipnpb.paypal.com/cgi-bin/webscr", query).as_str())
    })
    .await?;

    if block(move || validity.text()).await? != "verified" {
        return;
    }

    if payment_event.receiver_email != "redfreebird41@gmail.com" {
        return;
    }

    let client: Client = block(move || Client::new(format!("Bot {}", CONFIG.bot_token))).await?;
    let channel = client.channel(CONFIG.patron_channel).await?.unwrap();
    let member = client
        .guild_member(CONFIG.main_server, payment_event.custom.parse::<u64>()?)
        .await?;

    if member.is_none() {
        return;
    }

    let member = member.unwrap();
    let embed = EmbedBuilder::new()
        .title(format!("{} Payment", payment_event.payment_status))
        .field(EmbedFieldBuilder::new(
            "User",
            format!(
                "{}#{} ({})",
                member.user.name, member.user.discriminator, member.user.id
            ),
        ))
        .field(EmbedFieldBuilder::new(
            "Customer",
            format!(
                "{} {} ({})",
                payment_event.first_name, payment_event.last_name, payment_event.payer_email
            ),
        ))
        .field(EmbedFieldBuilder::new(
            "Product",
            format!(
                "{}\nAmount: {} {}",
                payment_event.item_name, payment_event.last_name, payment_event.payer_email
            ),
        ))
        .color(0x1e90ff)
        .build()?; // TODO: add error handling in `routes/mod.rs`

    client.create_message(channel.id()).embed(embed).await?;

    // TODO: the rest
}
