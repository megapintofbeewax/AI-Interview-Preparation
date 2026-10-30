import asyncio
import os
import edge_tts

async def list_en_voices():
    voices = await edge_tts.list_voices()
    en_voices = [v for v in voices if v['Locale'] in ['en-US', 'en-GB']]
    print(f"Total en-US / en-GB voices found: {len(en_voices)}")
    for v in en_voices:
        print(f"{v['ShortName']:<26} | {v['Gender']:<6} | {v['FriendlyName']}")

if __name__ == "__main__":
    asyncio.run(list_en_voices())
