const config = require("./config.json");

const Discord = require("discord.js");
const bot = new Discord.Client();


bot.on("ready", async () => {
    bot.user.setStatus("online");
    bot.user.setActivity(config.status.name, { type: config.status.type });
    console.log(`${bot.user.username} is online!`);
});

let regex = /https:\/\/upgrade\.chat\/checkout\/\?s=[a-zA-Z0-9]+/g;

bot.on("message", async message => {
    if (!message) return;

    if (message.author.id === "543974987795791872" && message.embeds[0]) {
        message.delete();
        if (message.embeds[0].fields[0] && message.embeds[0].fields[0].name.startsWith("You are purchasing a role from:")) {
            let link = message.embeds[0].fields[0].value.match(regex)[0];
            let embed = new Discord.RichEmbed()
            embed.setTitle("Donation Link");
            embed.setDescription(`To purchase ModMail Premium, please go to [this link](${link}). Thank you.`);
            embed.setColor(0x1E90FF);
            embed.setFooter(message.embeds[0].title.replace("This Link is only for: @", "This link is only meant for @") + ".");
            message.channel.send(embed);
        }
    }
});

let monthly2 = "597619481904414731";
let lifetime2 = "597619591656636426";
let patrons2 = "576756461267451934";

let monthly5 = "597619734871277571";
let lifetime5 = "597619838004756501";
let patrons5 = "576754574346551306";

let monthly10 = "597619962663796736";
let lifetime10 = "597620073334833165";
let patrons10 = "576754671620980740";

bot.on("guildMemberUpdate", async (oldMember, member) => {
    if (oldMember.roles === member.roles) return;

    if (!member.roles.has(patrons2) && (member.roles.has(monthly2) || member.roles.has(lifetime2))) member.addRole(patrons2);
    else if (member.roles.has(patrons2) && !member.roles.has(monthly2) && !member.roles.has(lifetime2)) member.removeRole(patrons2);

    if (!member.roles.has(patrons5) && (member.roles.has(monthly5) || member.roles.has(lifetime5))) member.addRole(patrons5);
    else if (member.roles.has(patrons5) && !member.roles.has(monthly5) && !member.roles.has(lifetime5)) member.removeRole(patrons5);

    if (!member.roles.has(patrons10) && (member.roles.has(monthly10) || member.roles.has(lifetime10))) member.addRole(patrons10);
    else if (member.roles.has(patrons10) && !member.roles.has(monthly10) && !member.roles.has(lifetime10)) member.removeRole(patrons10);
});

process.on("unhandledRejection", err => console.error(err.stack));

bot.login(config.token);