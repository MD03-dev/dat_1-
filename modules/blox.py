import os
import json
import time
import signal
import threading
from datetime import datetime
from zlapi.models import Message
from zlapi.models import Message, MultiMsgStyle, MessageStyle
from PIL import Image, ImageDraw, ImageFont
import io
import random
import math

des = {
    'version': "3.1.0",
    'credits': "Hoàng Khánh Prime Cte",
    'description': "BLOX FRUITS",
    'power': "Admin"
}

# ==========================
# 🗺️ MAP AREAS/ISLANDS (SEA 1 - SEA 3)
# ==========================
SEAS = {
    "sea1": {
        "name": "🌊 BIỂN THỨ NHẤT (LV 1-700)",
        "unlock_beli": 0,
        "areas": {
            "pirate_starter": {
                "name": "🏝️ Đảo Khởi Đầu Hải Tặc",
                "unlock": 1,
                "level_range": "1-10",
                "enemies": ["Bandit", "Pirate"],
                "base_exp": 20,
                "base_beli": 50,
                "description": "Đảo khởi đầu cho các hải tặc mới"
            },
            "marine_starter": {
                "name": "⚓ Đảo Khởi Đầu Hải Quân",
                "unlock": 1,
                "level_range": "1-10",
                "enemies": ["Marine Recruit", "Marine Soldier"],
                "base_exp": 20,
                "base_beli": 50,
                "description": "Đảo khởi đầu cho hải quân"
            },
            "jungle": {
                "name": "🌴 Đảo Rừng",
                "unlock": 10,
                "level_range": "10-30",
                "enemies": ["Bandit", "Monkey", "Gorilla"],
                "base_exp": 35,
                "base_beli": 80,
                "description": "Rừng rậm với động vật hoang dã"
            },
            "pirate_village": {
                "name": "🏴‍☠️ Làng Hải Tặc",
                "unlock": 30,
                "level_range": "30-60",
                "enemies": ["Pirate Thug", "Brute"],
                "base_exp": 50,
                "base_beli": 120,
                "description": "Làng của các hải tặc"
            },
            "desert": {
                "name": "🏜️ Đảo Sa Mạc",
                "unlock": 60,
                "level_range": "60-90",
                "enemies": ["Desert Bandit", "Desert Officer"],
                "base_exp": 70,
                "base_beli": 150,
                "description": "Sa mạc khắc nghiệt"
            },
            "frozen_village": {
                "name": "❄️ Làng Băng Giá",
                "unlock": 90,
                "level_range": "90-120",
                "enemies": ["Snow Bandit", "Snowman"],
                "base_exp": 90,
                "base_beli": 180,
                "description": "Làng bị đóng băng vĩnh viễn"
            },
            "marineford": {
                "name": "🏰 Pháo Đài Hải Quân",
                "unlock": 120,
                "level_range": "120-150",
                "enemies": ["Chief Petty Officer"],
                "base_exp": 110,
                "base_beli": 220,
                "description": "Pháo đài hải quân vững chắc"
            },
            "lower_skylands": {
                "name": "☁️ Đảo Trên Trời - Tầng Dưới",
                "unlock": 150,
                "level_range": "150-200",
                "enemies": ["Sky Bandit"],
                "base_exp": 130,
                "base_beli": 250,
                "description": "Đảo bay trên trời"
            },
            "upper_skylands": {
                "name": "⛅ Đảo Trên Trời - Tầng Trên",
                "unlock": 200,
                "level_range": "200-300",
                "enemies": ["Dark Master"],
                "base_exp": 160,
                "base_beli": 300,
                "description": "Tầng cao nhất của đảo bay"
            },
            "prison": {
                "name": "🔒 Nhà Tù",
                "unlock": 300,
                "level_range": "300-350",
                "enemies": ["Prisoner", "Dangerous Prisoner"],
                "base_exp": 190,
                "base_beli": 350,
                "description": "Nhà tù giam giữ tội phạm"
            },
            "colosseum": {
                "name": "⚔️ Đấu Trường",
                "unlock": 350,
                "level_range": "350-400",
                "enemies": ["Toga Warrior", "Gladiator"],
                "base_exp": 220,
                "base_beli": 400,
                "description": "Đấu trường tử chiến"
            },
            "magma_village": {
                "name": "🌋 Làng Dung Nham",
                "unlock": 400,
                "level_range": "400-450",
                "enemies": ["Military Soldier", "Military Spy"],
                "base_exp": 250,
                "base_beli": 450,
                "description": "Làng bên sườn núi lửa"
            },
            "underwater_city": {
                "name": "🐠 Thành Phố Dưới Nước",
                "unlock": 450,
                "level_range": "450-550",
                "enemies": ["Fishman Warrior", "Fishman Commando"],
                "base_exp": 280,
                "base_beli": 500,
                "description": "Thành phố của người cá"
            },
            "fountain_city": {
                "name": "⛲ Thành Phố Đài Phun Nước",
                "unlock": 550,
                "level_range": "550-700",
                "enemies": ["Galley Pirate", "Galley Captain"],
                "base_exp": 320,
                "base_beli": 600,
                "description": "Thành phố với đài phun nước lớn"
            }
        }
    },
    "sea2": {
        "name": "🌊 BIỂN THỨ HAI (LV 700-1500)",
        "unlock_level": 700,
        "unlock_beli": 500000,
        "areas": {
            "kingdom_rose": {
                "name": "🌹 Vương Quốc Hoa Hồng",
                "unlock": 700,
                "level_range": "700-875",
                "enemies": ["Raider", "Mercenary"],
                "base_exp": 380,
                "base_beli": 700,
                "description": "Vương quốc tràn ngập hoa hồng"
            },
            "green_zone": {
                "name": "🍃 Khu Vực Xanh",
                "unlock": 875,
                "level_range": "875-950",
                "enemies": ["Marine Lieutenant", "Marine Captain"],
                "base_exp": 420,
                "base_beli": 800,
                "description": "Khu vực xanh mát"
            },
            "graveyard": {
                "name": "⚰️ Nghĩa Địa",
                "unlock": 950,
                "level_range": "950-1000",
                "enemies": ["Zombie", "Vampire"],
                "base_exp": 460,
                "base_beli": 900,
                "description": "Nghĩa địa đầy bất an"
            },
            "snow_mountain": {
                "name": "🏔️ Núi Tuyết",
                "unlock": 1000,
                "level_range": "1000-1100",
                "enemies": ["Snow Trooper", "Winter Warrior"],
                "base_exp": 500,
                "base_beli": 1000,
                "description": "Núi tuyết quanh năm"
            },
            "hot_cold": {
                "name": "🔥❄️ Nóng & Lạnh",
                "unlock": 1100,
                "level_range": "1100-1200",
                "enemies": ["Lab Subordinate", "Horned Warrior"],
                "base_exp": 550,
                "base_beli": 1100,
                "description": "Khu vực với hai thái cực nhiệt độ"
            },
            "cursed_ship": {
                "name": "🚢 Con Tàu Bị Nguyền",
                "unlock": 1200,
                "level_range": "1200-1325",
                "enemies": ["Ship Deckhand", "Ship Engineer", "Ship Steward"],
                "base_exp": 600,
                "base_beli": 1200,
                "description": "Con tàu bị nguyền rủa"
            },
            "ice_castle": {
                "name": "🏰 Lâu Đài Băng",
                "unlock": 1325,
                "level_range": "1325-1350",
                "enemies": ["Arctic Warrior", "Snow Lurker"],
                "base_exp": 650,
                "base_beli": 1300,
                "description": "Lâu đài làm hoàn toàn bằng băng"
            },
            "forgotten_island": {
                "name": "🏝️ Đảo Bị Lãng Quên",
                "unlock": 1350,
                "level_range": "1350-1425",
                "enemies": ["Sea Soldier", "Water Fighter"],
                "base_exp": 700,
                "base_beli": 1400,
                "description": "Đảo bị lãng quên trong lịch sử"
            },
            "factory": {
                "name": "🏭 Nhà Máy",
                "unlock": 700,
                "level_range": "700-1500",
                "enemies": ["Factory Staff"],
                "base_exp": 400,
                "base_beli": 750,
                "description": "Nhà máy sản xuất"
            }
        }
    },
    "sea3": {
        "name": "🌊 BIỂN THỨ BA (LV 1500-2800)",
        "unlock_level": 1500,
        "unlock_beli": 700000,
        "areas": {
            "port_town": {
                "name": "🏙️ Thành Phố Cảng",
                "unlock": 1500,
                "level_range": "1500-1600",
                "enemies": ["Pirate Millionaire", "Pistol Billionaire"],
                "base_exp": 750,
                "base_beli": 1500,
                "description": "Thành phố cảng nhộn nhịp"
            },
            "hydra_island": {
                "name": "🐉 Đảo Hydra",
                "unlock": 1600,
                "level_range": "1600-1800",
                "enemies": ["Dragon Crew Warrior", "Dragon Crew Archer"],
                "base_exp": 800,
                "base_beli": 1600,
                "description": "Đảo của rồng"
            },
            "great_tree": {
                "name": "🌳 Cây Đại Thụ",
                "unlock": 1800,
                "level_range": "1800-2000",
                "enemies": ["Marine Commodore", "Marine Rear Admiral"],
                "base_exp": 850,
                "base_beli": 1700,
                "description": "Cây khổng lồ nghìn tuổi"
            },
            "floating_turtle": {
                "name": "🐢 Rùa Bay",
                "unlock": 2000,
                "level_range": "2000-2200",
                "enemies": ["Jungle Pirate", "Musketeer Pirate"],
                "base_exp": 900,
                "base_beli": 1800,
                "description": "Con rùa khổng lồ bay trên trời"
            },
            "haunted_castle": {
                "name": "👻 Lâu Đài Ma Ám",
                "unlock": 2200,
                "level_range": "2200-2400",
                "enemies": ["Reborn Skeleton", "Living Zombie", "Demon"],
                "base_exp": 950,
                "base_beli": 1900,
                "description": "Lâu đài bị ma ám"
            },
            "sea_of_treats": {
                "name": "🍭 Biển Kẹo Ngọt",
                "unlock": 2400,
                "level_range": "2400-2600",
                "enemies": ["Candy Rebel", "Sweet Thief"],
                "base_exp": 1000,
                "base_beli": 2000,
                "description": "Thế giới làm bằng kẹo"
            },
            "tiki_outpost": {
                "name": "🗿 Tiền Đồn Tiki",
                "unlock": 2600,
                "level_range": "2600-2800",
                "enemies": ["Tiki Warrior", "Tiki Spearman"],
                "base_exp": 1050,
                "base_beli": 2100,
                "description": "Tiền đồn với tượng Tiki"
            },
            "castle_on_sea": {
                "name": "🏰 Lâu Đài Trên Biển",
                "unlock": 2600,
                "level_range": "2600-2800",
                "enemies": ["Elite Pirate"],
                "base_exp": 1100,
                "base_beli": 2200,
                "description": "Lâu đài xây trên biển"
            }
        }
    }
}

# ==========================
# 🐉 DEVIL FRUITS - Danh sách đầy đủ
# ==========================
DEVIL_FRUITS = {
    "Dragon": {
        "name": "🐉 Dragon",
        "rarity": "mythical",
        "price": 5000000,
        "effects": {"damage": 50, "defense": 30, "speed": 20}
    },
    "Kitsune": {
        "name": "🦊 Kitsune",
        "rarity": "mythical",
        "price": 4500000,
        "effects": {"damage": 45, "defense": 25, "speed": 25}
    },
    "T Rex": {
        "name": "🦖 T-Rex",
        "rarity": "mythical",
        "price": 4000000,
        "effects": {"damage": 55, "defense": 20, "speed": 15}
    },
    "Mammoth": {
        "name": "🐘 Mammoth",
        "rarity": "mythical",
        "price": 3800000,
        "effects": {"damage": 60, "defense": 35, "speed": 10}
    },
    "Leopard": {
        "name": "🐆 Leopard",
        "rarity": "legendary",
        "price": 3500000,
        "effects": {"damage": 40, "defense": 15, "speed": 40}
    },
    "Yeti": {
        "name": "❄️ Yeti",
        "rarity": "legendary",
        "price": 3200000,
        "effects": {"damage": 42, "defense": 25, "speed": 18}
    },
    "Gas": {
        "name": "💨 Gas",
        "rarity": "legendary",
        "price": 3000000,
        "effects": {"damage": 38, "defense": 20, "speed": 22}
    },
    "Spirit": {
        "name": "👻 Spirit",
        "rarity": "legendary",
        "price": 2800000,
        "effects": {"damage": 35, "defense": 22, "speed": 25}
    },
    "Venom": {
        "name": "☠️ Venom",
        "rarity": "legendary",
        "price": 2500000,
        "effects": {"damage": 48, "defense": 18, "speed": 20}
    },
    "Control": {
        "name": "🌀 Control",
        "rarity": "legendary",
        "price": 2400000,
        "effects": {"damage": 32, "defense": 28, "speed": 20}
    },
    "Shadow": {
        "name": "🌑 Shadow",
        "rarity": "legendary",
        "price": 2300000,
        "effects": {"damage": 41, "defense": 15, "speed": 30}
    },
    "Dough": {
        "name": "🍞 Dough",
        "rarity": "epic",
        "price": 2000000,
        "effects": {"damage": 44, "defense": 22, "speed": 19}
    },
    "Blizzard": {
        "name": "🌨️ Blizzard",
        "rarity": "epic",
        "price": 1800000,
        "effects": {"damage": 40, "defense": 25, "speed": 15}
    },
    "Phoenix": {
        "name": "🔥 Phoenix",
        "rarity": "epic",
        "price": 1700000,
        "effects": {"damage": 42, "defense": 20, "speed": 23}
    },
    "Portal": {
        "name": "🚪 Portal",
        "rarity": "epic",
        "price": 1600000,
        "effects": {"damage": 30, "defense": 15, "speed": 40}
    },
    "Rumble": {
        "name": "⚡ Rumble",
        "rarity": "epic",
        "price": 1500000,
        "effects": {"damage": 45, "defense": 18, "speed": 22}
    },
    "Pain": {
        "name": "💀 Pain",
        "rarity": "epic",
        "price": 1400000,
        "effects": {"damage": 46, "defense": 16, "speed": 24}
    },
    "Love": {
        "name": "💖 Love",
        "rarity": "epic",
        "price": 1300000,
        "effects": {"damage": 35, "defense": 25, "speed": 25}
    },
    "String": {
        "name": "🕸️ String",
        "rarity": "rare",
        "price": 1200000,
        "effects": {"damage": 38, "defense": 20, "speed": 22}
    },
    "Paw": {
        "name": "🐾 Paw",
        "rarity": "rare",
        "price": 1100000,
        "effects": {"damage": 36, "defense": 22, "speed": 24}
    },
    "Quake": {
        "name": "🌋 Quake",
        "rarity": "rare",
        "price": 1000000,
        "effects": {"damage": 50, "defense": 25, "speed": 10}
    },
    "Buddha": {
        "name": "🪷 Buddha",
        "rarity": "rare",
        "price": 900000,
        "effects": {"damage": 55, "defense": 35, "speed": 5}
    },
    "Light": {
        "name": "💡 Light",
        "rarity": "rare",
        "price": 850000,
        "effects": {"damage": 40, "defense": 15, "speed": 35}
    },
    "Magma": {
        "name": "🌋 Magma",
        "rarity": "rare",
        "price": 800000,
        "effects": {"damage": 48, "defense": 22, "speed": 15}
    },
    "Ice": {
        "name": "🧊 Ice",
        "rarity": "common",
        "price": 750000,
        "effects": {"damage": 35, "defense": 30, "speed": 15}
    },
    "Sand": {
        "name": "🏜️ Sand",
        "rarity": "common",
        "price": 700000,
        "effects": {"damage": 38, "defense": 25, "speed": 17}
    },
    "Dark": {
        "name": "🌑 Dark",
        "rarity": "common",
        "price": 650000,
        "effects": {"damage": 42, "defense": 20, "speed": 18}
    },
    "Flame": {
        "name": "🔥 Flame",
        "rarity": "common",
        "price": 600000,
        "effects": {"damage": 45, "defense": 15, "speed": 20}
    },
    "Rubber": {
        "name": "🛞 Rubber",
        "rarity": "common",
        "price": 550000,
        "effects": {"damage": 30, "defense": 40, "speed": 20}
    },
    "Barrier": {
        "name": "🛡️ Barrier",
        "rarity": "common",
        "price": 500000,
        "effects": {"damage": 20, "defense": 50, "speed": 10}
    },
    "Diamond": {
        "name": "💎 Diamond",
        "rarity": "common",
        "price": 450000,
        "effects": {"damage": 25, "defense": 45, "speed": 10}
    },
    "Revive": {
        "name": "💫 Revive",
        "rarity": "common",
        "price": 400000,
        "effects": {"damage": 15, "defense": 20, "speed": 35}
    },
    "Bomb": {
        "name": "💣 Bomb",
        "rarity": "common",
        "price": 350000,
        "effects": {"damage": 50, "defense": 10, "speed": 20}
    },
    "Spike": {
        "name": "🌵 Spike",
        "rarity": "common",
        "price": 300000,
        "effects": {"damage": 40, "defense": 25, "speed": 15}
    },
    "Chop": {
        "name": "🔪 Chop",
        "rarity": "common",
        "price": 250000,
        "effects": {"damage": 35, "defense": 30, "speed": 15}
    },
    "Spring": {
        "name": "🦘 Spring",
        "rarity": "common",
        "price": 200000,
        "effects": {"damage": 25, "defense": 20, "speed": 40}
    },
    "Spin": {
        "name": "🌀 Spin",
        "rarity": "common",
        "price": 150000,
        "effects": {"damage": 30, "defense": 25, "speed": 25}
    },
    "Rocket": {
        "name": "🚀 Rocket",
        "rarity": "common",
        "price": 100000,
        "effects": {"damage": 20, "defense": 15, "speed": 45}
    },
    "Kilo-Kilo": {
        "name": "⚖️ Kilo-Kilo",
        "rarity": "common",
        "price": 50000,
        "effects": {"damage": 25, "defense": 35, "speed": 20}
    }
}

# ==========================
# 🥊 COMBAT STYLES SHOP
# ==========================
COMBAT_SHOP = {
    "Combat": {
        "name": "🥊 Combat",
        "price": 0,
        "sea": "sea1",
        "damage": 10
    },
    "Dark-Step": {
        "name": "👣 Dark-Step",
        "price": 150000,
        "sea": "sea1",
        "damage": 25
    },
    "Electric": {
        "name": "⚡ Electric",
        "price": 500000,
        "sea": "sea1",
        "damage": 35
    },
    "Water-Kung-Fu": {
        "name": "💧 Water-Kung-Fu",
        "price": 750000,
        "sea": "sea1",
        "damage": 45
    },
    "Black-Leg": {
        "name": "🦵 Black-Leg",
        "price": 0,
        "sea": "sea1",
        "damage": 20
    },
    "Electro": {
        "name": "⚡ Electro",
        "price": 0,
        "sea": "sea1",
        "damage": 30
    },
    "Dragon-Breath": {
        "name": "🐲 Dragon-Breath",
        "price": 1500000,
        "sea": "sea2",
        "damage": 60
    },
    "Sharkman-Karate": {
        "name": "🦈 Sharkman-Karate",
        "price": 2500000,
        "sea": "sea2",
        "damage": 90
    },
    "Superhuman": {
        "name": "💪 Superhuman",
        "price": 3000000,
        "sea": "sea2",
        "damage": 75
    },
    "Death-Step": {
        "name": "💀 Death-Step",
        "price": 2500000,
        "sea": "sea2",
        "damage": 90
    },
    "Electric-Claw": {
        "name": "🐾 Electric-Claw",
        "price": 3000000,
        "sea": "sea3",
        "damage": 130
    },
    "Dragon-Talon": {
        "name": "🐉 Dragon-Talon",
        "price": 3000000,
        "sea": "sea3",
        "damage": 120
    },
    "Godhuman": {
        "name": "👑 Godhuman",
        "price": 5000000,
        "sea": "sea3",
        "damage": 160
    },
    "Hoàng Khánh Primeuine-Art": {
        "name": "🩸 Hoàng Khánh Primeuine-Art",
        "price": 5000000,
        "sea": "sea3",
        "damage": 150
    }
}

# ==========================
# ⚡ UPGRADES SYSTEM
# ==========================
UPGRADES = {
    "melee": {
        "name": "🥊 Melee Damage",
        "max": 100,
        "base_price": 1000,
        "effect": "+2% sát thương cận chiến mỗi cấp",
        "multiplier": 1.5
    },
    "money": {
        "name": "💰 Money Multiplier",
        "max": 50,
        "base_price": 2000,
        "effect": "+3% vàng nhận được mỗi cấp",
        "multiplier": 2.0
    },
    "slot": {
        "name": "🎒 Inventory Slot",
        "max": 20,
        "base_price": 5000,
        "effect": "+1 ô chứa trái mỗi cấp",
        "multiplier": 3.0
    }
}

# ==========================
# 🎯 DAILY FRUITS (Random pool)
# ==========================
DAILY_FRUITS_POOL = [
    "Venom", "Control", "Shadow", "Dough", "Blizzard",
    "Phoenix", "Portal", "Rumble", "Pain", "Love",
    "String", "Paw", "Quake", "Light", "Magma",
    "Ice", "Sand", "Dark", "Flame", "Rubber",
    "Barrier", "Diamond", "Revive", "Bomb", "Spike",
    "Chop", "Spring", "Spin", "Rocket", "Kilo-Kilo"
]

ADMIN_ID = "789382913243202989"

BASE_DIR = "modules/data/blox"
DATA_FILE = os.path.join(BASE_DIR, "blox_data.json")
COOLDOWN_FILE = os.path.join(BASE_DIR, "blox_cooldowns.json")
LEADERBOARD_FILE = os.path.join(BASE_DIR, "blox_leaderboard.json")

# ==========================
# 📊 GLOBAL VARIABLES
# ==========================
player_data = {}
global_leaderboard = {}
active_commands = {}

# ==========================
# 🖼️ PLAYER INFO IMAGE GENERATOR
# ==========================
def generate_player_info_image(player, uid, target_player=None):
    img = Image.new("RGB", (900, 700), color=(20, 30, 45))
    draw = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 36)
        font_text = ImageFont.truetype("arial.ttf", 24)
        font_small = ImageFont.truetype("arial.ttf", 20)
        font_big = ImageFont.truetype("arial.ttf", 42)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_big = ImageFont.load_default()
    
    # Title
    title = "🏴‍☠️ HỒ SƠ BLOX FRUITS 🏴‍☠️" if not target_player else f"🏴‍☠️ HỒ SƠ {target_player.get('name', 'Người chơi')} 🏴‍☠️"
    draw.text((20, 20), title, font=font_title, fill=(255, 200, 50))
    
    # Player Info
    draw.text((20, 80), f"👤 ID: {uid}", font=font_text, fill=(220, 220, 220))
    
    # Level with MAX indicator
    level = player['level']
    exp = player['exp']
    exp_needed = level * 100 if level < 2800 else 0
    
    if level >= 2800:
        level_text = f"⚡ Cấp độ: {level} MAX"
    else:
        level_text = f"⚡ Cấp độ: {level} ({exp}/{exp_needed})"
    
    draw.text((20, 120), level_text, font=font_text, fill=(255, 255, 200))
    
    # Beli
    draw.text((20, 160), f"💰 Beli: {player['beli']:,}", font=font_text, fill=(255, 255, 100))
    
    # Sea and Area
    sea_id = player.get('sea', 'sea1')
    area_id = player.get('area', 'pirate_starter')
    sea_info = SEAS.get(sea_id, SEAS['sea1'])
    area_info = sea_info['areas'].get(area_id, sea_info['areas']['pirate_starter'])
    
    draw.text((20, 200), f"🌊 Sea: {sea_info['name'].split('(')[0].strip()}", font=font_text, fill=(180, 220, 255))
    draw.text((20, 240), f"🏝️ Đảo: {area_info['name']}", font=font_text, fill=(255, 200, 180))
    
    # Combat Style
    combat_style = player['combat']
    combat_info = COMBAT_SHOP.get(combat_style, COMBAT_SHOP['Combat'])
    draw.text((20, 280), f"🥊 Võ: {combat_info['name']}", font=font_text, fill=(180, 255, 180))
    
    # Devil Fruit
    fruit_name = "Không có" if player['devil_fruit'] is None else DEVIL_FRUITS[player['devil_fruit']]['name']
    draw.text((20, 320), f"🍎 Trái Ác Quỷ: {fruit_name}", font=font_text, fill=(255, 180, 180))
    
    # Stats
    draw.text((450, 80), "📊 THỐNG KÊ CHIẾN ĐẤU:", font=font_text, fill=(255, 255, 255))
    
    stats = player['stats']
    draw.text((450, 120), f"⚔️ Quái hạ gục: {stats.get('kills', 0)}", font=font_text, fill=(200, 200, 200))
    draw.text((450, 160), f"🎯 Boss đánh bại: {stats.get('boss_kills', 0)}", font=font_text, fill=(255, 220, 150))
    draw.text((450, 200), f"🏝️ Đảo đã đến: {stats.get('islands_visited', 1)}", font=font_text, fill=(150, 200, 255))
    draw.text((450, 240), f"🍎 Trái sưu tập: {stats.get('fruits_collected', 0)}", font=font_text, fill=(255, 150, 150))
    
    # Damage Info
    base_damage = combat_info['damage']
    melee_level = player['upgrades'].get('melee', 0)
    fruit_bonus = DEVIL_FRUITS[player['devil_fruit']]['effects']['damage'] if player['devil_fruit'] else 0
    total_damage = int(base_damage * (1 + melee_level * 0.02) + fruit_bonus)
    
    draw.text((450, 280), f"💥 Tổng sát thương: {total_damage}", font=font_text, fill=(255, 100, 100))
    
    # Money Multiplier
    money_level = player['upgrades'].get('money', 0)
    multiplier = 1 + (money_level * 0.03)
    draw.text((450, 320), f"💰 Nhân vàng: x{multiplier:.2f}", font=font_text, fill=(100, 255, 100))
    
    # Inventory
    bag_count = len(player.get('inventory', []))
    slot_level = player['upgrades'].get('slot', 0)
    max_slots = 1 + slot_level
    
    draw.text((20, 380), f"🎒 Túi đồ: {bag_count}/{max_slots}", font=font_text, fill=(255, 255, 255))
    
    # Show fruits in inventory
    y_pos = 420
    inventory = player.get('inventory', [])
    for i, fruit_id in enumerate(inventory[:5]):  # Show first 5
        if fruit_id in DEVIL_FRUITS:
            fruit = DEVIL_FRUITS[fruit_id]
            draw.text((20, y_pos), f"  {fruit['name']}", font=font_small, fill=(200, 255, 200))
            y_pos += 30
    
    if len(inventory) > 5:
        draw.text((20, y_pos), f"  ... và {len(inventory) - 5} trái khác", font=font_small, fill=(150, 150, 150))
    
    # Upgrades
    draw.text((450, 380), "⚡ NÂNG CẤP:", font=font_text, fill=(255, 255, 255))
    upgrades = player.get('upgrades', {})
    y = 420
    
    for upgrade_id, upgrade_info in UPGRADES.items():
        level = upgrades.get(upgrade_id, 0)
        draw.text((450, y), f"{upgrade_info['name']}: Lv {level}/{upgrade_info['max']}", font=font_small, fill=(200, 255, 200))
        y += 30
    
    # Random Cost
    random_cost = player.get('random_cost', 0)
    draw.text((20, 600), f"🎲 Giá random: {random_cost:,} Beli", font=font_small, fill=(150, 200, 255))
    
    # Daily Status
    daily_time = player.get('daily_time', 0)
    now = time.time()
    if now - daily_time < 1800:  # 30 minutes
        remaining = 1800 - (now - daily_time)
        draw.text((450, 600), f"⏳ Daily còn lại: {int(remaining/60)} phút", font=font_small, fill=(255, 200, 100))
    else:
        draw.text((450, 600), "✅ Có thể nhận daily!", font=font_small, fill=(100, 255, 100))
    
    # Footer
    draw.text((20, 660), f"🕒 Cập nhật: {datetime.now().strftime('%H:%M:%S')}", font=font_small, fill=(150, 150, 150))
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# ==========================
# 📁 FILE MANAGEMENT
# ==========================
def ensure_data_files():
    os.makedirs(BASE_DIR, exist_ok=True)
    for path in [DATA_FILE, COOLDOWN_FILE, LEADERBOARD_FILE]:
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)

def load_json(path):
    ensure_data_files()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_json(path, data):
    ensure_data_files()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_cooldowns():
    cd = load_json(COOLDOWN_FILE)
    return clean_cooldowns(cd)

def clean_cooldowns(cooldowns):
    now = int(time.time() * 1000)
    valid = {uid: ts for uid, ts in cooldowns.items() if ts > now}
    return valid

def save_cooldowns(cooldowns):
    cooldowns = clean_cooldowns(cooldowns)
    save_json(COOLDOWN_FILE, cooldowns)

def load_player_data():
    global player_data
    player_data = load_json(DATA_FILE)

def save_player_data():
    save_json(DATA_FILE, player_data)

def auto_save_loop():
    while True:
        time.sleep(300)
        try:
            save_player_data()
            save_cooldowns(load_cooldowns())
        except Exception:
            pass

threading.Thread(target=auto_save_loop, daemon=True).start()

def graceful_exit(*_):
    save_player_data()
    save_cooldowns(load_cooldowns())
    exit(0)

signal.signal(signal.SIGINT, graceful_exit)
signal.signal(signal.SIGTERM, graceful_exit)

# ==========================
# 👤 PLAYER FUNCTIONS
# ==========================
def get_player(data, uid, profile_data=None):
    if uid not in data:
        # Get player name from profile data
        player_name = "Người dùng"
        if profile_data and 'name' in profile_data:
            player_name = profile_data['name']
        
        data[uid] = {
            "name": player_name,
            "level": 1,
            "exp": 0,
            "beli": 1000,
            "combat": "Combat",
            "devil_fruit": None,
            "sea": "sea1",
            "area": "pirate_starter",
            "inventory": [],
            "stats": {
                "kills": 0,
                "boss_kills": 0,
                "islands_visited": 1,
                "fruits_collected": 0
            },
            "upgrades": {
                "melee": 0,
                "money": 0,
                "slot": 0
            },
            "random_cost": 0,
            "daily_time": 0,
            "last_hunt": 0
        }
    
    return data[uid]

def add_exp(player, amount):
    if player["level"] >= 2800:
        return 0  # Already at max level
    
    player["exp"] += amount
    level_up = 0
    exp_needed = player["level"] * 100
    
    while player["exp"] >= exp_needed and player["level"] < 2800:
        player["exp"] -= exp_needed
        player["level"] += 1
        level_up += 1
        exp_needed = player["level"] * 100
        
        # Cap at level 2800
        if player["level"] >= 2800:
            player["exp"] = 0
            break
    
    return level_up

def mention_text(uid, text):
    tag = f"@{uid}"
    return Message(text=f"{tag} {text}", mention=[{"tag": tag, "id": uid}])

# ==========================
# 🎮 MAIN COMMAND HANDLER
# ==========================
def handle_blox_command(message, message_object, thread_id, thread_type, author_id, client):
    global player_data
    msg = message.strip().lower()
    parts = msg.split()
    cmd = parts[1] if len(parts) > 1 else "help"
    uid = str(author_id)
    
    # Get profile data for name
    profile_data = {}
    
    # LOAD DATA
    cooldowns = load_cooldowns()
    player = get_player(player_data, uid, profile_data)
    now_ms = int(time.time() * 1000)
    
    # COOLDOWN CHECK for hunt
    base_cooldown = 2000  # 2 seconds for hunt
    
    if cmd == "hunt" and uid in cooldowns and cooldowns[uid] > now_ms:
        wait_s = (cooldowns[uid] - now_ms) / 1000
        client.sendMessage(Message(text=f"⏳ Chờ {wait_s:.1f}s để hunt tiếp!"), thread_id=thread_id, thread_type=thread_type)
        return
    
    # ====== COMMANDS ======
    if cmd == "help":
        help_text = (
            "🏴‍☠️ BLOX FRUITS-Hoàng Khánh Prime Cte 🏴‍☠️\n\n"
            "📜 LỆNH CHÍNH:\n"
            "• blox hunt → Đánh quái 🎯\n"
            "• blox eat <ID> → Ăn trái blox 🍎\n"
            "• blox map → Xem bản đồ & di chuyển 🗺️\n"
            "• blox random → Random trái 🎲\n"
            "• blox shop → Xem cửa hàng 🛒\n"
            "• blox bag → Xem balo 🎒\n"
            "• blox starts → Nâng cấp chỉ số ⚡\n"
            "• blox i4 → Xem hồ sơ cá nhân 📋\n"
            "• blox i4 like <@tag/uid> → LIKE hồ sơ 👤\n"
            "• blox rank → Xem BXH 🏆\n"
            "• blox daily → Nhận 1 trái blox 🎁\n"
            "• blox sea → Chuyển sea 🌊\n\n"
            
            "📖 CÁCH CHƠI:\n"
            "• Gõ blox cachchoi để xem hướng dẫn chi tiết\n\n"

        )
        client.sendMessage(Message(text=help_text), thread_id=thread_id, thread_type=thread_type)
        return
    
    if cmd == "cachchoi" or cmd == "cach":
        guide_text = (
            "📚 HƯỚNG DẪN CHI TIẾT BLOX FRUITS 📚\n\n"
            
            "🎯 CÁCH CHƠI CƠ BẢN:\n"
            "1. Bắt đầu với 1,000 Beli và võ Combat\n"
            "ĐÂY LÀ BẢN THỬ NGHIỆM BLOX FRUIT NẾU CÓ TRẢI NGHIỆM GÌ KHÔNG HÀI LÒNG XIN BẠN IB Hoàng Khánh Prime Cte VÀ GÓP Ý KIẾN CHO BẠN ẤY TIẾP TỤC CẤP NHẬT GAME:D\n"
            "2. Dùng 'blox hunt' để đánh quái, nhận EXP và Beli\n"
            "3. Lên cấp để mở khóa đảo mới\n"
            "4. Thu thập trái ác quỷ để tăng sức mạnh\n"
            "5. Nâng cấp để trở nên mạnh hơn\n\n"
            
            "🗺️ HỆ THỐNG BẢN ĐỒ:\n"
            "• Có 3 biển (Sea 1-3)\n"
            "• Sea 1: Level 1-700\n"
            "• Sea 2: Level 700-1500 (cần 500,000 Beli)\n"
            "• Sea 3: Level 1500-2800 (cần 700,000 Beli)\n"
            "• Mỗi biển có nhiều đảo\n"
            "• Đảo càng cao, quái càng mạnh, thưởng càng nhiều\n"
            "• Cần đủ level để vào đảo mới\n"
            "• Gõ 'blox map' để xem và di chuyển\n\n"
            
            "🍎 TRÁI ÁC QUỶ:\n"
            "• Có 35 loại trái với độ hiếm khác nhau\n"
            "• Mỗi trái có bonus sát thương, phòng thủ, tốc độ\n"
            "• Chỉ có thể ăn 1 trái cùng lúc\n"
            "• Có thể lưu trữ trái trong balo\n\n"
            
            "🥊 VÕ CÔNG (SHOP):\n"
            "• Bắt đầu với Combat (miễn phí)\n"
            "• Các võ khác cần mua bằng Beli\n"
            "• Mỗi sea có các võ khác nhau\n"
            "• Võ càng mạnh, sát thương càng cao\n"
            "• Gõ 'blox shop' để xem và mua võ\n\n"
            
            "⚡ NÂNG CẤP:\n"
            "• Melee: Tăng sát thương cận chiến\n"
            "• Money: Tăng Beli nhận được\n"
            "• Slot: Tăng ô chứa trái trong balo\n\n"
            
            "🎁 HỆ THỐNG THƯỞNG:\n"
            "• Daily: Nhận trái ngẫu nhiên mỗi 30 phút\n"
            "• Random: Random trái (free lần đầu)\n"
            "• Rank: Bảng xếp hạng toàn server\n\n"
            
            "⚠️ LƯU Ý QUAN TRỌNG:\n"
            "• Max level là 2800\n"
            "• Khi đạt 2800 sẽ hiển thị 'MAX'\n"
            "• Beli không bị mất khi chết\n"
            "• Có thể reset chỉ số nhưng tốn Beli\n"
            "• Balo ban đầu chỉ chứa được 1 trái mỗi loại\n"
            "• Nâng cấp slot để chứa thêm trái cùng loại\n"
        )
        client.sendMessage(Message(text=guide_text), thread_id=thread_id, thread_type=thread_type)
        return
    
    # 🎯 HUNT (Đánh quái)
    if cmd == "hunt":
        # Get current area info
        sea_id = player['sea']
        area_id = player['area']
        sea_info = SEAS.get(sea_id, SEAS['sea1'])
        area_info = sea_info['areas'].get(area_id, sea_info['areas']['pirate_starter'])
        
        # Check if player can hunt in this area
        if player['level'] < area_info['unlock']:
            client.sendMessage(
                Message(text=f"🔒 Cần level {area_info['unlock']} để hunt ở {area_info['name']}!"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return
        
        # Calculate rewards
        base_exp = area_info['base_exp']
        base_beli = area_info['base_beli']
        
        # Apply money multiplier
        money_level = player['upgrades'].get('money', 0)
        money_multiplier = 1 + (money_level * 0.03)
        
        # Apply level bonus
        level_bonus = 1 + (player['level'] / 1000)
        
        # Calculate final rewards
        exp_gain = int(base_exp * level_bonus * random.uniform(0.8, 1.2))
        beli_gain = int(base_beli * money_multiplier * level_bonus * random.uniform(0.8, 1.2))
        
        # Add rewards
        player['beli'] += beli_gain
        player['stats']['kills'] = player['stats'].get('kills', 0) + 1
        
        # Check for level up
        level_up = add_exp(player, exp_gain)
        
        # Check for area unlock notification
        new_area_unlocked = False
        unlock_message = ""
        
        # Check if player can move to next area
        for sea_key, sea in SEAS.items():
            for area_key, area in sea['areas'].items():
                if area['unlock'] == player['level']:
                    new_area_unlocked = True
                    unlock_message = f"🔓 Đã mở khóa {area['name']} (Level {area['unlock']}+)!"
                    break
            if new_area_unlocked:
                break
        
        # Check if player can move to next sea
        if sea_id == "sea1" and player['level'] >= 700 and player['beli'] >= 500000:
            new_area_unlocked = True
            unlock_message = f"🌊 Đã mở khóa {SEAS['sea2']['name']}! Gõ 'blox sea 2' để chuyển biển."
        elif sea_id == "sea2" and player['level'] >= 1500 and player['beli'] >= 700000:
            new_area_unlocked = True
            unlock_message = f"🌊 Đã mở khóa {SEAS['sea3']['name']}! Gõ 'blox sea 3' để chuyển biển."
        
        # Set cooldown
        cooldowns[uid] = now_ms + base_cooldown
        save_json(COOLDOWN_FILE, cooldowns)
        
        # Prepare message
        enemy = random.choice(area_info['enemies'])
        
        msg_lines = [
            f"🎯 HUNT THÀNH CÔNG!",
            "",
            f"🌊 Sea: {sea_info['name'].split('(')[0].strip()}",
            f"📍 Khu vực: {area_info['name']}",
            f"👾 Quái: {enemy}",
            "",
            "🎁 PHẦN THƯỞNG:",
            f"💰 +{beli_gain:,} Beli",
            f"✨ +{exp_gain} EXP",
            "",
            f"⚡ Level {player['level']} | EXP: {player['exp']}/{(player['level'] * 100) if player['level'] < 2800 else 0}",
            f"💰 Tổng Beli: {player['beli']:,}",
            f"🎯 Quái hạ: {player['stats']['kills']:,}",
        ]
        
        if player['level'] >= 2800:
            msg_lines.append(f"🏆 ĐẠT MAX LEVEL 2800! 🏆")
        
        if level_up > 0:
            msg_lines.append(f"\n🎉 LÊN CẤP {player['level']}! 🎉")
        
        if new_area_unlocked:
            msg_lines.append(f"\n{unlock_message}")
        
        msg = "\n".join(msg_lines)
        
        client.sendMessage(
            mention_text(uid, msg),
            thread_id=thread_id,
            thread_type=thread_type,
            ttl=10000
        )
        
        save_player_data()
        return
    
    # 🍎 EAT DEVIL FRUIT
    if cmd == "eat" and len(parts) >= 3:
        fruit_id = parts[2]
        
        # Check if fruit exists
        if fruit_id not in DEVIL_FRUITS:
            client.sendMessage(
                Message(text=f"❌ Không có trái '{fruit_id}'! Gõ 'blox bag' để xem trái bạn có."),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return
        
        # Check if player has the fruit
        if fruit_id not in player.get('inventory', []):
            client.sendMessage(
                Message(text=f"❌ Bạn không có trái {DEVIL_FRUITS[fruit_id]['name']} trong balo!"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return
        
        # Check if already have a fruit equipped
        if player['devil_fruit'] is not None:
            old_fruit = player['devil_fruit']
            # Move old fruit to inventory
            player['inventory'].append(old_fruit)
            
        # Equip new fruit
        player['devil_fruit'] = fruit_id
        
        # Remove from inventory
        player['inventory'].remove(fruit_id)
        
        # Update stats
        player['stats']['fruits_collected'] = player['stats'].get('fruits_collected', 0) + 1
        
        save_player_data()
        
        fruit_info = DEVIL_FRUITS[fruit_id]
        msg = f"✅ Đã ăn {fruit_info['name']}!\n"
        msg += f"💥 +{fruit_info['effects']['damage']} sát thương\n"
        msg += f"🛡️ +{fruit_info['effects']['defense']} phòng thủ\n"
        msg += f"⚡ +{fruit_info['effects']['speed']} tốc độ"
        
        client.sendMessage(Message(text=msg), thread_id=thread_id, thread_type=thread_type)
        return
    
    # 🗺️ MAP
    if cmd == "map":
        if len(parts) == 2:
            # Show map for current sea
            current_sea = player['sea']
            current_area = player['area']
            sea_info = SEAS[current_sea]
            
            map_text = f"🗺️ BẢN ĐỒ {sea_info['name']} 🗺️\n\n"
            
            for area_id, area_info in sea_info['areas'].items():
                # Check if area is unlocked
                area_unlocked = player['level'] >= area_info['unlock']
                current = (area_id == current_area)
                
                if current:
                    prefix = "📍 "
                elif area_unlocked:
                    prefix = "✅ "
                else:
                    prefix = "🔒 "
                
                map_text += f"{prefix}{area_info['name']} (Lv {area_info['unlock']}+) - {area_info['level_range']}\n"
                map_text += f"   {area_info['description']}\n\n"
            
            map_text += f"\n📍 Đang ở: {sea_info['areas'][current_area]['name']}\n"
            map_text += "➡️ Gõ: blox map <tên_đảo> để di chuyển\n"
            map_text += "🌊 Gõ: blox sea để chuyển biển"
            
            client.sendMessage(Message(text=map_text), thread_id=thread_id, thread_type=thread_type)
            return
        
        # Move to area
        if len(parts) >= 3:
            target_area_name = " ".join(parts[2:]).lower()
            target_found = False
            target_sea = player['sea']
            target_area = None
            
            # Search for area in current sea
            sea_info = SEAS.get(target_sea, SEAS['sea1'])
            for area_id, area_info in sea_info['areas'].items():
                area_name_lower = area_info['name'].lower()
                if target_area_name in area_name_lower or target_area_name == area_id:
                    target_found = True
                    target_area = area_id
                    break
            
            if not target_found:
                client.sendMessage(
                    Message(text="❌ Không tìm thấy đảo! Gõ 'blox map' để xem danh sách đảo trong sea hiện tại."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return
            
            # Check if area is unlocked
            area_info = sea_info['areas'][target_area]
            if player['level'] < area_info['unlock']:
                client.sendMessage(
                    Message(text=f"🔒 Cần level {area_info['unlock']} để vào {area_info['name']}!"),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return
            
            # Move player
            old_area = sea_info['areas'][player['area']]['name']
            player['area'] = target_area
            
            # Update stats
            player['stats']['islands_visited'] = player['stats'].get('islands_visited', 0) + 1
            
            save_player_data()
            
            msg = f"🚢 Di chuyển từ {old_area} đến {area_info['name']} thành công!"
            client.sendMessage(Message(text=msg), thread_id=thread_id, thread_type=thread_type)
            return
    
    # 🎲 RANDOM FRUIT
    if cmd == "random":
        # Check level requirement
        if player['level'] < 10:
            client.sendMessage(
                Message(text="🔒 Cần level 10 để random trái!"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return
        
        # Get random cost
        random_cost = player.get('random_cost', 0)
        
        # Check if first time (free)
        if random_cost == 0:
            # First time is free
            pass
        elif player['beli'] < random_cost:
            client.sendMessage(
                Message(text=f"❌ Không đủ Beli! Cần {random_cost:,} Beli."),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return
        else:
            # Deduct beli
            player['beli'] -= random_cost
        
        # Increase cost for next time (increase by 7,000 each time)
        player['random_cost'] = random_cost + 7000
        
        # Random fruit (weighted by rarity)
        rarity_weights = {
            "mythical": 5,
            "legendary": 15,
            "epic": 25,
            "rare": 35,
            "common": 50
        }
        
        # Create weighted list
        weighted_fruits = []
        for fruit_id, fruit_info in DEVIL_FRUITS.items():
            weight = rarity_weights.get(fruit_info['rarity'], 10)
            weighted_fruits.extend([fruit_id] * weight)
        
        # Select random fruit
        selected_fruit = random.choice(weighted_fruits)
        fruit_info = DEVIL_FRUITS[selected_fruit]
        
        # Check if player already has this fruit in inventory
        slot_level = player['upgrades'].get('slot', 0)
        max_same_fruit = 1 + slot_level
        
        # Count how many of this fruit player already has
        current_count = player['inventory'].count(selected_fruit)
        
        if current_count >= max_same_fruit:
            client.sendMessage(
                Message(text=f"❌ Đã có {max_same_fruit} trái {fruit_info['name']} trong balo! Nâng cấp slot để chứa thêm."),
                thread_id=thread_id,
                thread_type=thread_type
            )
            # Refund if not free
            if random_cost > 0:
                player['beli'] += random_cost
            player['random_cost'] = max(0, random_cost - 7000)
            save_player_data()
            return
        
        # Add to inventory
        player['inventory'].append(selected_fruit)
        
        # Update stats
        player['stats']['fruits_collected'] = player['stats'].get('fruits_collected', 0) + 1
        
        save_player_data()
        
        msg = f"🎲 RANDOM THÀNH CÔNG!\n\n"
        msg += f"🍎 Nhận được: {fruit_info['name']}\n"
        msg += f"⭐ Độ hiếm: {fruit_info['rarity'].upper()}\n"
        msg += f"💰 Giá trị: {fruit_info['price']:,} Beli\n\n"
        msg += f"💥 Bonus: +{fruit_info['effects']['damage']} damage\n"
        msg += f"🛡️ Bonus: +{fruit_info['effects']['defense']} defense\n"
        msg += f"⚡ Bonus: +{fruit_info['effects']['speed']} speed\n\n"
        msg += f"🎒 Đã thêm vào balo! ({current_count + 1}/{max_same_fruit})\n"
        msg += f"💸 Lần random tiếp: {player['random_cost']:,} Beli"
        
        client.sendMessage(Message(text=msg), thread_id=thread_id, thread_type=thread_type)
        return
    
    # 🛒 SHOP (Combat Styles)
    if cmd == "shop":
        current_sea = player['sea']
        
        if len(parts) == 2:
            # Show shop for current sea
            shop_text = f"🛒 CỬA HÀNG VÕ THUẬT - {SEAS[current_sea]['name']} 🛒\n\n"
            
            for style_id, style_info in COMBAT_SHOP.items():
                # Show only styles available in current sea or lower
                if style_info['sea'] == current_sea or (
                    current_sea == "sea2" and style_info['sea'] == "sea1") or (
                    current_sea == "sea3" and style_info['sea'] in ["sea1", "sea2"]):
                    
                    owned = "✅" if player['combat'] == style_id else "⚪"
                    price_text = f"{style_info['price']:,} Beli" if style_info['price'] > 0 else "MIỄN PHÍ"
                    
                    shop_text += f"{owned} {style_info['name']}\n"
                    shop_text += f"   💰 Giá: {price_text}\n"
                    shop_text += f"   💥 Sát thương: {style_info['damage']}\n"
                    shop_text += f"   🌊 Sea: {style_info['sea'].replace('sea', 'Sea ')}\n"
                    shop_text += f"   🛒 Gõ: blox shop {style_id}\n\n"
            
            shop_text += f"\n🥊 Đang dùng: {COMBAT_SHOP[player['combat']]['name']}\n"
            shop_text += "💡 Gõ 'blox shop <ID_võ>' để mua"
            
            client.sendMessage(Message(text=shop_text), thread_id=thread_id, thread_type=thread_type)
            return
        
        # Buy combat style
        if len(parts) >= 3:
            style_id = parts[2]
            
            if style_id not in COMBAT_SHOP:
                client.sendMessage(
                    Message(text="❌ Không có võ này trong cửa hàng!"),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return
            
            style_info = COMBAT_SHOP[style_id]
            
            # Check if already owned
            if player['combat'] == style_id:
                client.sendMessage(
                    Message(text=f"✅ Bạn đã sở hữu {style_info['name']} rồi!"),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return
            
            # Check if player is in correct sea
            current_sea = player['sea']
            style_sea = style_info['sea']
            
            sea_order = {"sea1": 1, "sea2": 2, "sea3": 3}
            if sea_order.get(style_sea, 0) > sea_order.get(current_sea, 0):
                client.sendMessage(
                    Message(text=f"🔒 Cần ở {style_sea.replace('sea', 'Sea ')} để mua {style_info['name']}!"),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return
            
            # Check if player has enough beli
            if player['beli'] < style_info['price']:
                client.sendMessage(
                    Message(text=f"❌ Không đủ Beli! Cần {style_info['price']:,} Beli."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return
            
            # Buy the style
            player['beli'] -= style_info['price']
            player['combat'] = style_id
            
            save_player_data()
            
            msg = f"✅ Mua thành công {style_info['name']}!\n"
            msg += f"💥 Sát thương: {style_info['damage']}\n"
            msg += f"💰 Còn lại: {player['beli']:,} Beli"
            
            client.sendMessage(Message(text=msg), thread_id=thread_id, thread_type=thread_type)
            return
    
    # 🎒 BAG (Inventory)
    if cmd == "bag":
        inventory = player.get('inventory', [])
        slot_level = player['upgrades'].get('slot', 0)
        max_slots = 1 + slot_level  # Base 1 slot + upgrades
        
        if not inventory:
            client.sendMessage(
                Message(text=f"🎒 Balo trống rỗng!\nÔ trống: {len(inventory)}/{max_slots}"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return
        
        # Group similar fruits and count
        grouped = {}
        for fruit_id in inventory:
            grouped[fruit_id] = grouped.get(fruit_id, 0) + 1
        
        # Create display
        lines = [f"🎒 BALO CỦA BẠN ({len(inventory)}/{max_slots})\n"]
        
        total_value = 0
        for fruit_id, count in grouped.items():
            if fruit_id in DEVIL_FRUITS:
                fruit = DEVIL_FRUITS[fruit_id]
                total_value += fruit['price'] * count
                max_same = 1 + slot_level
                lines.append(f"{fruit['name']} x{count}/{max_same} - {fruit['price']:,} Beli")
        
        lines.append(f"\n💰 Tổng giá trị: {total_value:,} Beli")
        lines.append(f"🍎 Gõ 'blox eat <ID>' để ăn trái")
        lines.append(f"⚡ Nâng cấp slot để chứa thêm trái (hiện tại: {max_slots} ô)")
        lines.append(f"🎯 Có thể chứa tối đa {1 + slot_level} trái cùng loại")
        
        msg = "\n".join(lines)
        
        client.sendMessage(
            Message(text=msg),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return
    
    # ⚡ STARTS (Upgrades)
    if cmd == "starts":
        if len(parts) == 2:
            # Show upgrades list
            upgrades_text = "⚡ HỆ THỐNG NÂNG CẤP ⚡\n\n"
            
            for upgrade_id, upgrade_info in UPGRADES.items():
                current_level = player['upgrades'].get(upgrade_id, 0)
                next_level = current_level + 1
                
                if next_level > upgrade_info['max']:
                    price_text = "ĐẠT TỐI ĐA"
                else:
                    price = int(upgrade_info['base_price'] * (upgrade_info['multiplier'] ** current_level))
                    price_text = f"{price:,} Beli"
                
                upgrades_text += f"• {upgrade_info['name']}\n"
                upgrades_text += f"  Cấp hiện tại: {current_level}/{upgrade_info['max']}\n"
                upgrades_text += f"  Hiệu ứng: {upgrade_info['effect']}\n"
                upgrades_text += f"  Giá nâng cấp: {price_text}\n"
                upgrades_text += f"  Gõ: blox starts {upgrade_id}\n\n"
            
            client.sendMessage(Message(text=upgrades_text), thread_id=thread_id, thread_type=thread_type)
            return
        
        # Buy upgrade
        if len(parts) >= 3:
            upgrade_id = parts[2]
            
            if upgrade_id not in UPGRADES:
                client.sendMessage(
                    Message(text="❌ Không có nâng cấp này!"),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return
            
            upgrade_info = UPGRADES[upgrade_id]
            current_level = player['upgrades'].get(upgrade_id, 0)
            
            if current_level >= upgrade_info['max']:
                client.sendMessage(
                    Message(text=f"❌ {upgrade_info['name']} đã đạt cấp tối đa ({upgrade_info['max']})!"),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return
            
            # Calculate price
            price = int(upgrade_info['base_price'] * (upgrade_info['multiplier'] ** current_level))
            
            if player['beli'] < price:
                client.sendMessage(
                    Message(text=f"❌ Không đủ Beli! Cần {price:,} Beli."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return
            
            # Apply upgrade
            player['beli'] -= price
            player['upgrades'][upgrade_id] = current_level + 1
            
            save_player_data()
            
            msg = f"✅ Nâng cấp {upgrade_info['name']} lên cấp {current_level + 1} thành công!"
            
            # Add specific info for each upgrade
            if upgrade_id == "slot":
                new_max = 1 + (current_level + 1)
                msg += f"\n🎒 Giờ bạn có thể chứa tối đa {new_max} trái cùng loại!"
            elif upgrade_id == "money":
                new_multiplier = 1 + ((current_level + 1) * 0.03)
                msg += f"\n💰 Nhân vàng: x{new_multiplier:.2f}"
            elif upgrade_id == "melee":
                new_bonus = (current_level + 1) * 0.02
                msg += f"\n💥 Tăng sát thương: +{new_bonus*100:.0f}%"
            
            client.sendMessage(Message(text=msg), thread_id=thread_id, thread_type=thread_type)
            return
    
    # 📋 I4 (Profile)
    if cmd == "i4":
        target_uid = uid
        target_player = player
        target_profile_data = profile_data
        
        # Check if viewing someone else's profile
        if len(parts) >= 4 and parts[2] == "like":
            target_uid = parts[3].replace("@", "").strip()
            
            # Remove any non-numeric characters
            target_uid = ''.join(filter(str.isdigit, target_uid))
            
            if not target_uid:
                client.sendMessage(
                    Message(text="❌ ID không hợp lệ!"),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return
            
            # Get target player data
            target_player = get_player(player_data, target_uid)
            # Get target name from message if available
            target_profile_data = {'name': f"ID {target_uid}"}
        
        # Generate and send profile image
        buffer = generate_player_info_image(target_player, target_uid, target_profile_data)
        
        profile_text = f"📜 Hồ sơ {'của bạn' if target_uid == uid else f'người chơi ID {target_uid}'}:"
        
        client.sendLocalImage(
            image=buffer,
            message=Message(text=profile_text),
            thread_id=thread_id,
            thread_type=thread_type
        )
        return
    
    # 🏆 RANK
    if cmd == "rank":
        # Create leaderboard
        leaderboard_data = []
        
        for user_id, pdata in player_data.items():
            # Get player name
            player_name = pdata.get('name', f"ID {user_id}")
            
            leaderboard_data.append({
                'id': user_id,
                'name': player_name,
                'level': pdata.get('level', 1),
                'beli': pdata.get('beli', 0),
                'kills': pdata.get('stats', {}).get('kills', 0),
                'fruits': pdata.get('stats', {}).get('fruits_collected', 0)
            })
        
        # Sort by level (primary) and beli (secondary)
        sorted_players = sorted(leaderboard_data, key=lambda x: (x['level'], x['beli']), reverse=True)
        
        # Prepare rank message
        rank_text = "🏆 BẢNG XẾP HẠNG BLOX FRUITS 🏆\n\n"
        
        for i, p in enumerate(sorted_players[:10]):
            rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            emoji = rank_emoji[i] if i < 10 else f"{i+1}."
            
            # Truncate long names
            name = p['name']
            if len(name) > 15:
                name = name[:12] + "..."
            
            rank_text += f"{emoji} {name}\n"
            rank_text += f"   ⚡ Lv {p['level']} | 💰 {p['beli']:,} Beli\n"
            rank_text += f"   🎯 {p['kills']:,} kills | 🍎 {p['fruits']} trái\n\n"
        
        # Add player's own rank
        player_rank = None
        for i, p in enumerate(sorted_players):
            if p['id'] == uid:
                player_rank = i + 1
                break
        
        if player_rank:
            rank_text += f"\n📊 Xếp hạng của bạn: #{player_rank}"
        
        client.sendMessage(Message(text=rank_text), thread_id=thread_id, thread_type=thread_type)
        return
    
    # 🎁 DAILY
    if cmd == "daily":
        now = time.time()
        last_daily = player.get('daily_time', 0)
        
        # Check if 30 minutes have passed
        if now - last_daily < 1800:  # 30 minutes in seconds
            remaining = 1800 - (now - last_daily)
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            
            client.sendMessage(
                Message(text=f"⏳ Phải chờ {minutes} phút {seconds} giây nữa để nhận daily tiếp!"),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return
        
        # Select random fruit from daily pool
        selected_fruit = random.choice(DAILY_FRUITS_POOL)
        fruit_info = DEVIL_FRUITS[selected_fruit]
        
        # Check inventory space
        slot_level = player['upgrades'].get('slot', 0)
        max_same_fruit = 1 + slot_level
        current_count = player['inventory'].count(selected_fruit)
        
        if current_count >= max_same_fruit:
            client.sendMessage(
                Message(text=f"❌ Đã có {max_same_fruit} trái {fruit_info['name']} trong balo! Nâng cấp slot để chứa thêm."),
                thread_id=thread_id,
                thread_type=thread_type
            )
            return
        
        # Add to inventory
        player['inventory'].append(selected_fruit)
        
        # Update daily time
        player['daily_time'] = now
        
        # Update stats
        player['stats']['fruits_collected'] = player['stats'].get('fruits_collected', 0) + 1
        
        save_player_data()
        
        msg = f"🎁 NHẬN DAILY THÀNH CÔNG!\n\n"
        msg += f"🍎 Nhận được: {fruit_info['name']}\n"
        msg += f"⭐ Độ hiếm: {fruit_info['rarity'].upper()}\n"
        msg += f"💰 Giá trị: {fruit_info['price']:,} Beli\n\n"
        msg += f"💥 Bonus: +{fruit_info['effects']['damage']} damage\n"
        msg += f"🛡️ Bonus: +{fruit_info['effects']['defense']} defense\n"
        msg += f"⚡ Bonus: +{fruit_info['effects']['speed']} speed\n\n"
        msg += f"🎒 Đã thêm vào balo! ({current_count + 1}/{max_same_fruit})\n"
        msg += f"⏳ Có thể nhận daily tiếp sau 30 phút"
        
        client.sendMessage(Message(text=msg), thread_id=thread_id, thread_type=thread_type)
        return
    
    # 🌊 SEA (Change sea)
    if cmd == "sea":
        if len(parts) == 2:
            # Show sea info
            current_sea = player['sea']
            sea_info = SEAS[current_sea]
            
            sea_text = f"🌊 HỆ THỐNG BIỂN 🌊\n\n"
            sea_text += f"📍 Đang ở: {sea_info['name']}\n\n"
            
            for sea_id, sea in SEAS.items():
                unlocked = True
                requirements = []
                
                if sea_id == "sea1":
                    requirements.append("Bắt đầu game")
                elif sea_id == "sea2":
                    if player['level'] < 700:
                        unlocked = False
                        requirements.append(f"Level 700 (hiện: {player['level']})")
                    if player['beli'] < 500000:
                        unlocked = False
                        requirements.append(f"500,000 Beli (hiện: {player['beli']:,})")
                elif sea_id == "sea3":
                    if player['level'] < 1500:
                        unlocked = False
                        requirements.append(f"Level 1500 (hiện: {player['level']})")
                    if player['beli'] < 700000:
                        unlocked = False
                        requirements.append(f"700,000 Beli (hiện: {player['beli']:,})")
                
                prefix = "🌊 " if sea_id == current_sea else ("✅ " if unlocked else "🔒 ")
                sea_text += f"{prefix}{sea['name']}\n"
                
                if not unlocked and requirements:
                    sea_text += f"   Yêu cầu: {', '.join(requirements)}\n"
                
                sea_text += f"   Gõ: blox sea {sea_id.replace('sea', '')}\n\n"
            
            client.sendMessage(Message(text=sea_text), thread_id=thread_id, thread_type=thread_type)
            return
        
        # Change sea
        if len(parts) >= 3:
            sea_number = parts[2]
            target_sea = f"sea{sea_number}"
            
            if target_sea not in SEAS:
                client.sendMessage(
                    Message(text="❌ Chỉ có Sea 1, 2, 3! Gõ 'blox sea' để xem thông tin."),
                    thread_id=thread_id,
                    thread_type=thread_type
                )
                return
            
            # Check requirements
            sea_info = SEAS[target_sea]
            
            if target_sea == "sea2":
                if player['level'] < 700:
                    client.sendMessage(
                        Message(text=f"🔒 Cần level 700 để vào Sea 2! (hiện: {player['level']})"),
                        thread_id=thread_id,
                        thread_type=thread_type
                    )
                    return
                if player['beli'] < 500000:
                    client.sendMessage(
                        Message(text=f"🔒 Cần 500,000 Beli để vào Sea 2! (hiện: {player['beli']:,})"),
                        thread_id=thread_id,
                        thread_type=thread_type
                    )
                    return
            elif target_sea == "sea3":
                if player['level'] < 1500:
                    client.sendMessage(
                        Message(text=f"🔒 Cần level 1500 để vào Sea 3! (hiện: {player['level']})"),
                        thread_id=thread_id,
                        thread_type=thread_type
                    )
                    return
                if player['beli'] < 700000:
                    client.sendMessage(
                        Message(text=f"🔒 Cần 700,000 Beli để vào Sea 3! (hiện: {player['beli']:,})"),
                        thread_id=thread_id,
                        thread_type=thread_type
                    )
                    return
            
            # Change sea
            old_sea = player['sea']
            player['sea'] = target_sea
            
            # Reset to first area of new sea
            first_area = list(SEAS[target_sea]['areas'].keys())[0]
            player['area'] = first_area
            
            save_player_data()
            
            msg = f"🌊 Chuyển từ {SEAS[old_sea]['name']} đến {sea_info['name']} thành công!\n"
            msg += f"🏝️ Đã tự động chuyển đến đảo đầu tiên: {SEAS[target_sea]['areas'][first_area]['name']}"
            
            client.sendMessage(Message(text=msg), thread_id=thread_id, thread_type=thread_type)
            return
    
    # ❌ DEFAULT
    client.sendMessage(
        Message(text="❌ Lệnh không hợp lệ! Gõ 'blox help' để xem hướng dẫn."),
        thread_id=thread_id,
        thread_type=thread_type
    )

# ==========================
# 🚀 INIT SYSTEM
# ==========================
def initialize_blox_system():
    ensure_data_files()
    load_player_data()

initialize_blox_system()

# ==========================
# 📤 EXPORT FOR BOT
# ==========================
def PTA():
    return {
        "blox": handle_blox_command
    }