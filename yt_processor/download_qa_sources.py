#!/usr/bin/env python3
"""Download all sources from Hyperarch Fascia Q&A notebook"""
import json
import subprocess
from pathlib import Path

NOTEBOOK_ID = "4963d1f4-6003-4172-9772-1b4e1542b7fd"
OUTPUT_DIR = Path("../transcripts/Hyperarch_Fascia_QA_Sources")

# List of all 50 sources from the notebook
sources = [
    ("db617466-831e-4b16-8672-4894252aec2d", "Body Fat Plyometrics and Cauliflower Ears - QA Episode 9.mp3"),
    ("58e80306-58df-4ac3-991f-86c89b32ff3a", "Coffee The Tongue and How Long An HFT Session Should Go For - QA.mp3"),
    ("ef776465-ce76-4ccb-8489-24b819082d4f", "Does No Fap Affect Fascia QA Episode 10 Hyperarch Fascia Trainin.mp3"),
    ("4aa524b6-4319-4fc2-bdf8-8725b0cf0010", "HFT QA Episode 1 - What are your heels actually for Hyperarch Fa.mp3"),
    ("1fefc15b-155d-4c69-8c6c-3d0b20f04bcc", "How Fast Can A Foot Hyperarch Morph - QA Episode 11 Hyperarch Fa.mp3"),
    ("9e821670-aae4-4bb0-a2ad-be145e382c0b", "QA 19 Bloodflow Restriction Training Biteforce Arthritis Towel C.mp3"),
    ("0752b119-7536-4579-8204-a5e856d27bc4", "QA EP 18 Are Chiropractors Good How To Turn Fibroblast to Myofib.mp3"),
    ("3e37f573-535d-484a-8f17-1aee63722bc5", "QA EP 36 Quad Dominance Altitude Psoas TFL Is Fascia An Organ MO.mp3"),
    ("cad78af7-9191-4aa3-89a1-fbcd45f09203", "QA EP 37 Alcohol CR7 Hyaluronic Acid Towel Curls HFT in Football.mp3"),
    ("d7e8c970-bf68-4bf7-96ce-ce7ba4141f7d", "QA EP 39 Why Do My Quads Activate Muscle Guarding Toe Joints Veg.mp3"),
    ("cf68fb91-9b9e-468c-9c0f-0ca493ebf3be", "QA EP 48 Why are my glutes sore for days after HFT Does complete.mp3"),
    ("117f9917-c5ec-46a9-8950-ab391b533cf1", "QA EP 5- How Antidepressants Icebaths Saunas and Bike Riding Aff.mp3"),
    ("b340def7-ff9e-4385-8197-07a27e2592a3", "QA EPISODE 7 - When Are Weights Added In HFT Program Hyperarch F.mp3"),
    ("23fe292a-f386-42d3-a092-dd91c0b8353a", "QA Ep 14 - HFT In Socks Big Toe Important Can I do HFT Everyday.mp3"),
    ("0020a513-f0ad-41a4-a460-3c75213d33d8", "QA Ep 15 - Cracking Knuckles Proprioceptive Insoles Fibrosis Fro.mp3"),
    ("2becdc53-768a-4651-96d6-b29a9b0f02ce", "QA Ep 16 Modern Shoes Mushrooms Tea Calluses Breathing from the.mp3"),
    ("dbf5ec86-87b0-4890-9577-5c3681335acd", "QA Ep 17 - Fascia Nutrition Special Hyperarch Fascia Training.mp3"),
    ("af27be70-0f14-46e1-b7e2-a3ace9ee3e23", "QA Ep 20 Overcoming Isometrics In-Season HFT Sickness Cortisone.mp3"),
    ("5ac587d1-a92e-4295-b063-d753a92ac341", "QA Ep 21 - PROTOCOLS EDITION Hyperarch Fascia Training.mp3"),
    ("70a1718e-e95d-4964-903b-d592258cd0af", "QA Ep 22 HFT Patreon Program Toe Length Biomechanics Hand Fascia.mp3"),
    ("5d67d921-3cdf-438e-91f4-49fb61f29f20", "QA Ep 23 How To Correctly Engage The Toes Hyperarch Fascia Train.mp3"),
    ("6620a63b-ff15-4fb4-a659-1c3e8b27316f", "QA Ep 24 Should You Take Collagen Hyperarch Lunge Importance Hyp.mp3"),
    ("c4252723-d4a5-4bb5-86ac-817204b7db37", "QA Ep 25 - Scoliosis Osgood Schlatter No Glute Response MORE Hyp.mp3"),
    ("decffc09-c11d-41ec-90ce-a3579916c79d", "QA Ep 26 Increase Testosterone Fast Twitch Muscles Lebron James.mp3"),
    ("091eccb4-8ad6-42a8-be90-3df707c8f131", "QA Ep 27 Hernias Optimal Joint Angles BOF Running PRP Hydrogel M.mp3"),
    ("3974f518-5ad1-4331-ba36-3d46f4e61306", "QA Ep 28 Jayson Tatum Injury Breakdown Hyperarch Meditation Reco.mp3"),
    ("dcd03854-cf2f-4f24-9e99-5ee614a4fef6", "QA Ep 29 - If Your Toes Wont Move What Should You Do Normatec De.mp3"),
    ("3f0d7674-1bed-42ee-a2bc-a90c95c07598", "QA Ep 30 Men Vs Women Foot Tension Hydrating The Fascia Global F.mp3"),
    ("70fc9018-54fd-40e7-96d6-dc49552a539b", "QA Ep 31 The Secret of HFT Stretches Is The Hyperarch Metamorpho.mp3"),
    ("d40fc2de-b6b6-46f4-976d-b60f3f236e79", "QA Ep 32 Why Legs Shake In HFT Linking Fascia and Qi Selecting F.mp3"),
    ("47a25cfd-95e4-47d1-930d-d3f99ed56db8", "QA Ep 33 Sand training Increasing Piezoelectricity Towel Curl Va.mp3"),
    ("1623c875-644c-4356-a29d-59dc3008aa99", "QA Ep 34 Instinct Bone Density Training Isometrics Pelvic Tilt M.mp3"),
    ("0b954e57-7ab5-4030-9e48-97cb3b393299", "QA Ep 35 HFT Meditation Posture Why the Marble Goes Under Second.mp3"),
    ("f7353964-3754-425c-b923-ced117b53a1f", "QA Ep 38 Flat Feet Spiky Ball Shoe Wear Pattern Eating Behaviour.mp3"),
    ("1cd361e3-4b18-401a-b5aa-9c22916059b3", "QA Ep 40 If I dont have a Foot to Glute connection what should I.mp3"),
    ("1e2aa258-b2b7-4b2c-847c-ce34b72fdc26", "QA Ep 41 How Important Is Fascia Rolling Walking. Can I Skip The.mp3"),
    ("d0c6db7e-6a91-481b-bd01-cca2048165fa", "QA Ep 42 After Achieving No Dysfunctions How Do I Progress Furth.mp3"),
    ("a75f2285-ac1f-4a1f-afec-a1dfc85369da", "QA Ep 43 Why Arent Single Leg Hyperarch Hops Included On Patreon.mp3"),
    ("5d6ee04b-30ab-42c1-87f5-e816b9a16f33", "QA Ep 44 How Does Fascia Help In Endurance Sports Turf Toe Ankle.mp3"),
    ("c291c321-97c8-4d44-9e17-6244e2d24ac8", "QA Ep 45 Does HFT Create Spiral Movements What actually is Tendo.mp3"),
    ("ef820a2c-a7c3-4bd2-9c1e-8b25e0755bba", "QA Ep 46 Is the big toe the main driver of the Hyperarch Mechani.mp3"),
    ("68bfb026-357b-4ff0-960c-bd152474fc15", "QA Ep 47 Can I unlock Flow State from being Hyperarch Fascia Dri.mp3"),
    ("695d88ca-4dcb-4ad0-b60c-3ef8cfa8993d", "QA Ep 49 Does HFT still work for FLAT FEET Why is the ATT so imp.mp3"),
    ("40965737-23bd-430d-b267-9c7eeb06456c", "QA Ep 50 Are calluses good Why do I only have half of the Hypera.mp4"),
    ("e6611263-f09e-4696-915b-9fe9aabf7023", "QA Episode 13 - The BIG MONEY Question... Hyperarch Fascia Train.mp3"),
    ("b006f889-de45-44cf-865b-c07064703724", "QA Episode 6 - What is the role of Muscle Hyperarch Fascia Train.mp3"),
    ("42288956-e87e-4532-ad22-32d793f08cf7", "Should You Wear Toe Spacers QA Episode 4 Hyperarch Fascia Traini.mp3"),
    ("15fca656-722b-4baf-9e03-a5cba418360c", "Stretching is GOOD and BAD -Members ONLY QA - Episode 2 Hyperarc.mp3"),
    ("1cf3c3fd-dc72-408c-b396-db48f14379e2", "Torn Ligaments Need This To Heal... QA EP 3 Hyperarch Fascia Tra.mp3"),
    ("64389eec-d53b-405e-bc2a-b72983b15c87", "UNMISSABLE EPISODE Calisthenics Cramps DOMS and Regeneration - Q.mp3"),
]

print(f"Downloading {len(sources)} sources from NotebookLM...")
print(f"Output directory: {OUTPUT_DIR}")
print()

for source_id, title in sources:
    output_file = OUTPUT_DIR / title.replace(" ", "_").replace("/", "_")
    print(f"Downloading: {title}")
    # Use notebooklm-mcp download_artifact
    result = subprocess.run(
        ["python", "-m", "notebooklm_mcp.download_artifact", 
         NOTEBOOK_ID, source_id, str(output_file)],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"  ✅ Downloaded: {output_file.name}")
    else:
        print(f"  ❌ Failed: {title}")
        print(f"     Error: {result.stderr}")

print("\n✅ Download complete!")
