import os
import math
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="/", intents=intents)

COLOR_DISTANCE = 0x3498DB
COLOR_QUERY = 0x2ECC71
COLOR_ERROR = 0xE74C3C


def calc_distance(ammo: float, angle: float) -> float:
    modified_angle = (2 * angle) % 180
    sin_val = math.sin(math.radians(modified_angle))
    power_val = (ammo * 200) ** 2
    return round((sin_val * power_val) / 196.2, 1)


def calc_angles(distance: float, ammo: float):
    target_sin = (distance * 196.2) / ((ammo * 200) ** 2)
    two_theta_deg = math.degrees(math.asin(target_sin))
    angle_low = round(two_theta_deg / 2)
    angle_high = 90 - angle_low
    return angle_low, angle_high


def max_distance_for_ammo(ammo: float) -> float:
    return round((ammo * 200) ** 2 / 196.2, 1)


@bot.event
async def on_ready():
    print(f"{bot.user} 已上線！")
    try:
        synced = await bot.tree.sync()
        print(f"已同步 {len(synced)} 個斜線指令")
    except Exception as e:
        print(f"同步失敗：{e}")


@bot.tree.command(name="c_d", description="輸入裝彈量與仰角，計算發射距離")
@app_commands.describe(ammo="推進藥量 (1→1.5→2→2.5→3→3.5→4→4.5→5→0.5)", angle="炮筒仰角 40~85")
async def c_d_cmd(interaction: discord.Interaction, ammo: float, angle: float):
    AMMO_LIST = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 0.5]
    if ammo not in AMMO_LIST:
        return await error_embed(interaction, "裝彈量必須為 1 / 1.5 / 2 / 2.5 / 3 / 3.5 / 4 / 4.5 / 5 / 0.5")
    if angle < 40 or angle > 85:
        return await error_embed(interaction, "仰角必須在 40 ~ 85 度之間")

    distance = calc_distance(ammo, angle)

    embed = discord.Embed(title="發射距離", color=COLOR_DISTANCE)
    embed.add_field(name="推進藥量", value=f"`{ammo}`", inline=True)
    embed.add_field(name="炮筒仰角", value=f"`{angle:g}°`", inline=True)
    embed.add_field(name="發射距離", value=f"**`{distance}`**", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="q_s", description="輸入目標距離，自動算出最佳裝彈量與仰角")
@app_commands.describe(distance="目標距離")
async def q_s_cmd(interaction: discord.Interaction, distance: float):
    if distance <= 0:
        return await error_embed(interaction, "目標距離必須大於 0")

    AMMO_LIST = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 0.5]
    max_possible = max_distance_for_ammo(max(AMMO_LIST))

    if distance > max_possible:
        embed = discord.Embed(title="距離無法到達", color=COLOR_ERROR)
        embed.add_field(name="目標距離", value=f"`{distance}`", inline=True)
        embed.add_field(name="最遠可達距離", value=f"**`{max_possible}`**（裝彈 5.0，仰角 45°）", inline=False)
        return await interaction.response.send_message(embed=embed)

    best = None
    best_error = float("inf")
    best_angle = float("inf")
    best_ammo_idx = float("inf")

    for ammo_idx, ammo in enumerate(AMMO_LIST):
        for angle in range(40, 86):
            actual = calc_distance(ammo, angle)
            error = abs(actual - distance)

            better = (
                error < best_error
                or (error == best_error and angle < best_angle)
                or (error == best_error and angle == best_angle and ammo_idx < best_ammo_idx)
            )

            if better:
                best_error = error
                best_angle = angle
                best_ammo_idx = ammo_idx
                best = (ammo, angle)

    ammo, angle = best
    embed = discord.Embed(title="建議配置", color=COLOR_QUERY)
    embed.add_field(name="目標距離", value=f"`{distance}`", inline=True)
    embed.add_field(name="推進藥量", value=f"`{ammo}`", inline=True)
    embed.add_field(name="炮筒仰角", value=f"**`{angle}°`**", inline=True)
    await interaction.response.send_message(embed=embed)


async def error_embed(interaction: discord.Interaction, message: str):
    embed = discord.Embed(title="錯誤", description=message, color=COLOR_ERROR)
    await interaction.response.send_message(embed=embed)


if __name__ == "__main__":
    if not TOKEN:
        print("錯誤：未設定 TOKEN，請檢查 .env 檔案")
    else:
        bot.run(TOKEN)
