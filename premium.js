const config = require("./config.json");
const Discord = require("discord.js");
const bot = new Discord.Client();

bot.on("ready", async () => {
    bot.user.setStatus("online");
    bot.user.setActivity(config.status.name, { type: config.status.type });
    console.log(`${bot.user.username} is online!`);
});

bot.on("message", async message => {
    if (!message) return;
    if (["donate", "premium", "purchase"].includes(message.content.toLowerCase())) {
        let embed = new Discord.RichEmbed()
        embed.setTitle("Donation Link");
        embed.setDescription(`To purchase ModMail Premium, please go to [this link](${"https://donatebot.io/checkout/576016832956334080?buyer=" + message.author.id}). Thank you.`);
        embed.setColor(0x1E90FF);
        embed.setFooter(`This link is only meant for ${message.author.tag}`);
        message.channel.send(embed);
    }
});

process.on("unhandledRejection", err => console.error(err.stack));

bot.login(config.token);
