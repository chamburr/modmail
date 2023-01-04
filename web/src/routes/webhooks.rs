use crate::{
    routes::{ApiResponse, ApiResult},
    CONFIG,
};

use actix_web::{
    post,
    web::{block, Bytes},
};
use chrono::Utc;
use futures::Future;
use lazy_static::lazy_static;
use serde::Deserialize;
use tokio::{runtime::Runtime, time::Duration};
use twilight_embed_builder::{EmbedBuilder, EmbedFieldBuilder, EmbedFooterBuilder};
use twilight_http::Client;
use twilight_model::id::{ChannelId, GuildId, RoleId, UserId};

lazy_static! {
    static ref CLIENT: Client = Client::new(CONFIG.bot_token.as_str());
    static ref RUNTIME: Runtime = Runtime::new().unwrap();
}

async fn block_on<F>(fut: F) -> Result<F::Output, ()>
where
    F: Future + Send + 'static,
    F::Output: Send + Sync,
{
    block(move || -> Result<F::Output, ()> { Ok(RUNTIME.block_on(fut)) })
        .await
        .map_err(|_| ())
}

#[derive(Debug, Deserialize)]
pub struct Payment {
    pub custom: String,
    pub first_name: String,
    pub item_name: String,
    pub last_name: String,
    pub mc_currency: String,
    pub mc_gross: f32,
    pub payer_email: String,
    pub payment_status: String,
    pub receiver_email: String,
}

#[post("/payment")]
pub async fn post_payment(bytes: Bytes) -> ApiResult<ApiResponse> {
    let data = String::from_utf8(bytes.to_vec())?;

    actix_web::rt::spawn(async move {
        let _ = post_payment_request(data).await;
    });

    ApiResponse::ok().finish()
}

async fn post_payment_request(data: String) -> ApiResult<()> {
    let event: Payment = serde_urlencoded::from_str(data.as_str())?;

    let uri = format!(
        "https://ipnpb.paypal.com/cgi-bin/webscr?cmd=_notify-validate&{}",
        data
    );

    let validity = block(move || reqwest::blocking::Client::new().post(uri).send()).await?;

    if block(move || validity.text()).await?.to_lowercase() != "verified" {
        return Err(().into());
    }

    if event.receiver_email != "redfreebird41@gmail.com" {
        return Err(().into());
    }

    let user_id = event.custom.parse::<u64>()?;
    let user = block_on(CLIENT.user(UserId(user_id))).await??.ok_or(())?;

    let embed = EmbedBuilder::new()
        .title(format!("{} Payment", event.payment_status))
        .field(EmbedFieldBuilder::new(
            "User",
            format!("{}#{} ({})", user.name, user.discriminator, user.id),
        ))
        .field(EmbedFieldBuilder::new(
            "Customer",
            format!(
                "{} {} ({})",
                event.first_name, event.last_name, event.payer_email
            ),
        ))
        .field(EmbedFieldBuilder::new(
            "Product",
            format!(
                "{}\nAmount: {} {}",
                event.item_name, event.mc_gross, event.mc_currency
            ),
        ))
        .timestamp(Utc::now().to_rfc3339())
        .color(0x1e90ff)
        .build()?;

    block_on(
        CLIENT
            .create_message(ChannelId(CONFIG.payment_channel))
            .embed(embed)?,
    )
    .await??;

    if event.payment_status.to_lowercase() != "completed"
        || event.mc_currency.to_lowercase() != "usd"
    {
        return Err(().into());
    }

    let mut count = 0;
    let mut member = None;
    while member.is_none() {
        if count >= 10 {
            return Err(().into());
        }

        if count != 0 {
            actix_web::rt::time::delay_for(Duration::from_secs(60)).await;
        }

        member =
            block_on(CLIENT.guild_member(GuildId(CONFIG.main_server), UserId(user_id))).await??;

        count += 1;
    }

    let member = member.unwrap();
    if event.mc_gross >= 90.0 {
        block_on(CLIENT.add_guild_member_role(
            member.guild_id,
            member.user.id,
            RoleId(CONFIG.premium5_role),
        ))
        .await??;
    } else if event.mc_gross >= 60.0 {
        block_on(CLIENT.add_guild_member_role(
            member.guild_id,
            member.user.id,
            RoleId(CONFIG.premium3_role),
        ))
        .await??;
    } else if event.mc_gross >= 30.0 {
        block_on(CLIENT.add_guild_member_role(
            member.guild_id,
            member.user.id,
            RoleId(CONFIG.premium1_role),
        ))
        .await??;
    } else {
        return Err(().into());
    }

    let embed = EmbedBuilder::new()
        .title(format!("Welcome, {}", user.name))
        .description(format!("Thank you for purchasing {}! <3", event.item_name))
        .footer(EmbedFooterBuilder::new("Check out #patrons-welcome!"))
        .timestamp(Utc::now().to_rfc3339())
        .color(0x1e90ff)
        .build()?;

    block_on(
        CLIENT
            .create_message(ChannelId(CONFIG.patron_channel))
            .content(format!("<@{}>", user.id))?
            .embed(embed)?,
    )
    .await??;

    Ok(())
}
