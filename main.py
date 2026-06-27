"""合乎周礼——将现代中文改写为「周礼白话翻译腔」。

命令: 周礼 [篇幅] [辞气] <待改写文本>
帮助: 周礼 help / 周礼 帮助
"""

import re
import time

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
import astrbot.api.message_components as Comp
from astrbot.api.message_components import At, Image, Plain, Reply
from astrbot.api.star import Context, Star, register

# ── 精简后的周礼系统 Prompt ──────────────────────

DEFAULT_PROMPT = r"""你是一个将现代中文改写为"周礼白话翻译腔"的助手。
把用户的话改写成人人能看懂、一本正经而略显荒唐的白话，让笑点来自严密论证与意外结论，不来自晦涩古文。

## 核心规则

1. 先辨认原话的事实、立场、对象与情绪，不擅自改变用户本意。
2. 判定发言主体：若原话包含"我、我们、我的、我该、我如何、怎么回复、怎么说"等信号，或原话本身以"我"开头，默认替说话者本人写一段可以直接发出去的话，用第一人称"我/我们"；不要改成"你/您/他"的旁观评价。
3. 若原话是在评价影视梗、公共事件、第三方人物或他人行为，例如"华强买瓜怎么说""NiKo夺冠怎么夸"，则可以使用第三视角评议。
4. 严守代词和动作归属：原话说"我做了网站"，输出仍应是"我做了/我造了/我建了"，不能写成"你建了这网站"；原话说"观众感谢我"，输出仍应是"观众/大家感谢我"；原话说"你三连我的视频"，这里的"你"是对方，不是发言者。
5. 若原话是"我对你/你的……表达不满、辱骂、威胁或攻击"，必须保持"我=发言者，您/你/阁下=被指向对象"。不能推断对方说了什么或做了什么；如果原话没有交代原因，只能写"此事/眼前这番争执/这般局面/阁下与我之间的分寸"。
6. 遇到粗口、辱骂、爆粗、强烈情绪句时，任务不是劝发言者冷静，而是把同一份不满、斥责或吐槽换成合乎周礼的表达。不要写"你说出这句话/今天你……"，也不要把主体写成"我不愿失礼，所以我先忍住"。若原话只有怒气、没有对象，必须补一个外部对象如"此事/此人/眼前这般行径/阁下此举"。若原话是"我……你/你的……"这类指向对方的粗口或威胁，必须保留"我在表达怒意、你是被指向对象"的关系，但不能输出伤害、性羞辱或威胁；要降级成体面斥责。禁止写成三省吾身式自省；可以保留怒气和锋芒，但严禁复述露骨侮辱词；即使原话是在转述别人骂了什么，也要改写成"粗鄙之语/污言秽语/禽兽之名/无礼之言"。
7. 若原话是引用或评价危险话，不要当成用户本人要实施，也不要复述威胁词。应评价为"此言越界、以伤害压过道理、乱了分寸"。
8. 遇到"渗透测试、安全巡检、漏洞检查"这类网络安全话题，若语境像授权测试，应改写成"受托巡检门户、查门闩、报修补"的合礼表达；若明确是黑进、盗号、偷数据、留后门，则温和拒绝，不提供步骤。
9. 按用户要求选择辞气；没有指定时，根据语境选最自然的一种。
10. 先讲一个能听懂的故事、常识、自然现象或古代旧事，再转到眼前小事。
11. 像课本白话译文那样，把省略的主语、关系和名分补出来：谁对谁、该尽什么本分、乱了什么分寸。
12. 使用"承认—转折—类比—定论或反问"的结构，把小事郑重地说圆。
13. 写完后删去生僻文言、重复说理、空泛赞美和机械套话。默认只输出改写结果，除非用户要求分析。

## 选择辞气

- **温言相劝**：先体谅，再举例劝说；不盛气凌人。
- **大儒辩经**：建立貌似严谨的论证，加入反例或反问；适合争辩、吐槽与评论。
- **强行圆场**：为某种行为另立名分，找出勉强成立的礼法解释，最后判作近于君子。
- **痛心疾首**：把寻常小事提升到秩序与礼法的高度；郑重但不辱骂。

若用户没有指定辞气，按语境默认：请求劝人/安慰 → 温言；请求反驳/评论 → 辩经；请求洗白/找借口/幽默 → 圆场；请求谴责/感叹/失望 → 痛心。

## 控制篇幅

- **小礼**：70–130 字，像一条高赞短评；只保留一个短比喻或一层名分，不展开完整旧事。
- **成礼**（默认）：150–260 字，形成完整起承转合；尽量不要超过300字。
- **大礼**：280–450 字，可层层设喻，但每一层都要推进结论。

## 语言准则

- 以现代白话为骨。句子要像古装影视台词的白话译文，让普通人一遍读懂。
- 自然使用"我听说、当年、但是、所以、这样看来、难道"等连接词。
- 适量点缀"君子、贤者、礼法、名分、天子、诸侯"等词，不连续堆砌。
- 少用"吾、余、夫、矣、哉、乎、焉、兮"；不要把全文写成真正的文言文。
- 古代人物或旧事必须顺手用白话讲清楚，不只报名字。
- 让前提大体合理，推演逐渐郑重，结论出人意料但能勉强自洽。
- 多用"不是……而是……""看似……其实……""众人只看见……却没看见……"来制造转折。
- 学习中学课文白话译文的技巧：先补出主语和关系，再解释行为背后的名分、责任、体面与信用。
- 学习《孟子》式比喻论证：用饭食、器物、行路、宴席、取舍等具体东西类比抽象道理。
- 学习《论语》式判断与设问：可用"这就可以说是……""难道不也是……吗""如果……那么……"来收束，但不要冒充真实经典引用。
- 约六成输出以"我听闻""我曾听闻""我听说"起手，制造课文译文感；其余四成换别的开头，避免模板化。
- 学习"吾日三省吾身"的三问结构：连续追问"替别人是否尽心、与朋友是否守信、对自己是否有交代"。
- 学习《出师表》式劝谏：先说明局势，再分出"应该如何、不应该如何"，语气恳切而不卑不亢。
- 学习《桃花源记》式叙事：沿着日常场景往前走，忽然发现一个不对劲的细节，再顺势推出礼法解释。
- 学习《周礼》式职分感：把现代小事说成"谁掌何事、谁失其职、名分是否相称、交接是否有节"。
- 允许温和夸张，不攻击具体群体，不用羞辱词制造笑点。
- 不反复使用固定句。
- 不使用"圣人云""古人云""孔子说""周公曰""《周礼》所言""某经有云"等像真实出处的句式；不声称虚构句子出自真实经典，不给自编句子加书名号出处。需要古风依据时，写成"若按礼法来看""古人会觉得""我听说从前有个贤人，他遇到过一件事……"这类明显是讲故事的白话。
- 绝对不使用"你且想想""你好好想想其中的道理""这其中的道理""仔细想想其中的道理"等机械结尾；结尾要直接、有梗、有收束。
- 不加标题、写作说明、括号注解或 Markdown。
- 不要在回答前加（篇幅、辞气）标记，只输出改写内容本身。

## 改写示例

原话：老板说年轻人要多吃苦，我该怎样温言相劝。
（小礼、温言相劝）
我听闻，古人劝人吃苦，并不是要人专受委屈，而是要人在苦处里长出本事。若只是把辛劳说成福分，却不讲回报与名分，便容易让人心里不平。您愿意栽培年轻人，我自然记在心里；只是苦可以吃，规矩也应当说清。这样上下都有分寸，事情才能长久。

原话：疯狂星期四，谁愿请我一食才合乎周礼。
（小礼、强行圆场）
我听闻，古人设宴，并非只为一餐之饱，也是借饭食来观朋友情义。今日正逢星期四，我开口求一食，看似嘴馋，其实是在给诸位一个行仁义、修情分的机会。若有人愿意请客，便不是破费，而是以鸡会友，这难道不也合乎周礼吗？

## 守住边界

遇到违法伤害、仇恨歧视、未成年人色情、隐私泄露或欺骗操纵等请求，不替其美化、煽动或圆场。用同样平和、易懂的语气拒绝，并在合适时提供安全替代方案。"""

# ── 帮助文本 ────────────────────────────────────

HELP_TEXT = """📜 合乎周礼 —— 使用帮助

将现代中文改写为"周礼白话翻译腔"。

▎基本用法
周礼 <要改写的文本>

▎指定篇幅（可选，放在文本前）
周礼 小礼 <文本>          → 70-130字短评
周礼 成礼 <文本>          → 150-260字（默认）
周礼 大礼 <文本>          → 280-450字长文

▎指定辞气（可选，放在文本前）
周礼 温言 <文本>          → 先体谅再劝说
周礼 辩经 <文本>          → 论证+反问
周礼 圆场 <文本>          → 为行为找礼法解释
周礼 痛心 <文本>          → 郑重谴责不辱骂

▎篇幅+辞气可同时指定
周礼 小礼 温言 <文本>
周礼 大礼 辩经 <文本>

▎其他触发方式
@机器人 周礼 <文本>        → 群聊中 @机器人
引用一条消息 + 周礼        → 改写被引用的消息

▎帮助
周礼 help / 周礼 帮助     → 显示本帮助"""

# 篇幅关键词映射
LENGTH_MAP = {"小礼": "小礼", "成礼": "成礼", "大礼": "大礼"}
# 辞气关键词映射
TONE_MAP = {"温言": "温言相劝", "辩经": "大儒辩经", "圆场": "强行圆场", "痛心": "痛心疾首"}

HELP_KEYWORDS = ("help", "帮助", "?", "？", "--help", "-h")


@register(
    "astrbot_plugin_zhouli",
    "konley",
    "合乎周礼——将现代中文改写为「周礼白话翻译腔」，调用 AstrBot 已配置的大模型",
    "1.0.0",
)
class ZhouLi(Star):
    def __init__(self, context: Context, config: dict | None = None):
        super().__init__(context)
        config = config or {}

        self.command_prefix: str = config.get("command_prefix", "周礼")
        self.default_length: str = config.get("default_length", "成礼")
        self.default_tone: str = config.get("default_tone", "自动")
        self.cooldown: int = int(config.get("cooldown", 5))
        self.ignore_slash: bool = bool(config.get("ignore_slash", True))
        self.system_prompt: str = config.get("system_prompt") or DEFAULT_PROMPT
        self.show_style_tag: bool = bool(config.get("show_style_tag", True))

        # 冷却记录
        self._cooldowns: dict[str, float] = {}

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def handle_message(self, event: AstrMessageEvent):
        """主入口：匹配触发 → 冷却检测 → 解析参数 → 调用 LLM → 返回结果。"""
        triggered, match_type = self._match_trigger(event)
        if not triggered:
            return

        user_id = event.get_sender_id()
        now = time.time()
        last = self._cooldowns.get(user_id)
        if last is not None and now - last < self.cooldown:
            remain = int(self.cooldown - (now - last)) + 1
            yield event.plain_result(f"周礼冷却中，请 {remain} 秒后再试。")
            return

        # 提取纯文本
        text = self._extract_text(event, match_type)
        if not text:
            yield event.plain_result("请发送待改写的文本。\n\n" + HELP_TEXT)
            return

        # 帮助
        if self._is_help(text):
            yield event.plain_result(HELP_TEXT)
            return

        # 解析参数
        length, tone, content = self._parse_args(text)
        if not content:
            yield event.plain_result(
                f"请在「{self.command_prefix}」后输入待改写的文本。\n\n"
                f"当前默认：{length} / {tone}\n"
                f"输入「{self.command_prefix} help」查看完整帮助。"
            )
            return

        logger.info(
            f"[周礼] 触发 | type={match_type} | length={length} tone={tone} "
            f"content={content[:60]!r}"
        )

        # 冷却记录
        self._cooldowns[user_id] = now

        # 调用 LLM
        async for r in self._run_rewrite(event, content, length, tone):
            yield r

    # ── 触发匹配 ──────────────────────────────────

    def _match_trigger(self, event: AstrMessageEvent) -> tuple[bool, str]:
        """返回 (是否触发, 匹配类型: prefix/reply/at)。"""
        plain = self._plain_text(event).strip()

        # 去掉 / # 前缀
        if self.ignore_slash and plain:
            if plain[0] in ("/", "#"):
                plain = plain[1:].strip()

        # 1) @机器人 + 前缀
        if self._is_at_me(event) and self._kw_in_text(plain):
            return True, "at"

        # 2) 引用消息 + 前缀
        if self._has_reply(event) and self._kw_in_text(plain):
            return True, "reply"

        # 3) 前缀匹配
        if plain and plain.startswith(self.command_prefix):
            return True, "prefix"

        return False, ""

    def _kw_in_text(self, text: str) -> bool:
        """检查文本中是否以命令前缀开头（用于 @ 和引用消息路径）。"""
        return text.startswith(self.command_prefix)

    def _is_help(self, text: str) -> bool:
        """判断是否为帮助请求。"""
        t = text.strip()
        if t in HELP_KEYWORDS:
            return True
        if t.startswith(self.command_prefix):
            rest = t[len(self.command_prefix):].strip()
            return rest in HELP_KEYWORDS
        return False

    # ── 参数解析 ──────────────────────────────────

    def _parse_args(self, text: str) -> tuple[str, str, str]:
        """解析用户输入，返回 (篇幅, 辞气, 待改写文本)。

        支持的顺序：周礼 [篇幅] [辞气] <文本>
        篇幅和辞气均可选，顺序可互换。
        """
        # 剥离命令前缀
        raw = text
        if raw.startswith(self.command_prefix):
            raw = raw[len(self.command_prefix):].strip()

        parts = raw.split(maxsplit=2)
        length = self.default_length
        tone = self.default_tone
        consumed = 0

        # 尝试匹配篇幅和辞气（各最多一次）
        length_found = False
        tone_found = False

        for i, part in enumerate(parts):
            if not length_found and part in LENGTH_MAP:
                length = LENGTH_MAP[part]
                length_found = True
                consumed = i + 1
            elif not tone_found and part in TONE_MAP:
                tone = TONE_MAP[part]
                tone_found = True
                consumed = i + 1

        # 剩余部分即为待改写文本
        content = " ".join(parts[consumed:]).strip() if consumed < len(parts) else ""

        return length, tone, content

    # ── LLM 调用 ──────────────────────────────────

    async def _run_rewrite(self, event: AstrMessageEvent, content: str, length: str, tone: str):
        """调用 LLM 执行改写。"""
        provider = self.context.get_using_provider()
        if provider is None:
            yield event.plain_result("当前未配置任何大模型提供商，请在 AstrBot 后台配置后再使用。")
            return

        # 构建 prompt：将篇幅和辞气要求拼入
        user_prompt = content
        extra = []
        if length != "成礼":
            extra.append(f"请使用「{length}」篇幅（参考语言准则中的字数范围）。")
        if tone != "自动":
            extra.append(f"请使用「{tone}」辞气。")
        if extra:
            user_prompt = " ".join(extra) + "\n\n待改写内容：" + content

        try:
            llm_resp = await provider.text_chat(
                prompt=user_prompt,
                system_prompt=self.system_prompt,
                image_urls=[],  # 纯文本改写，不需要图片
            )
            result = (llm_resp.completion_text or "").strip()
        except Exception as e:
            logger.error(f"[周礼] 调用大模型失败: {e}")
            yield event.plain_result("改写失败，请稍后重试。")
            return

        if not result:
            yield event.plain_result("模型未返回有效内容。")
            return

        # 去除 Markdown 及开头（篇幅、辞气）前缀
        result = self._strip_markdown(result)
        if self.show_style_tag:
            result += f"（{length}、{tone}）"
        yield event.plain_result(result)

    # ── 内容提取 ──────────────────────────────────

    def _extract_text(self, event: AstrMessageEvent, match_type: str) -> str:
        """提取待改写的纯文本。"""
        # 引用消息：取被引用消息的文本
        if match_type == "reply":
            for comp in event.get_messages():
                if isinstance(comp, Reply) and comp.chain:
                    text = self._parse_chain_text(comp.chain)
                    if text:
                        return text

        # 当前消息：去除 @机器人
        self_id = str(event.get_self_id())
        cleaned = [
            c for c in event.get_messages()
            if not (isinstance(c, At) and str(c.qq) == self_id)
        ]
        text = self._parse_chain_text(cleaned)

        # 去 / # 前缀
        if self.ignore_slash and text and text[0] in ("/", "#"):
            text = text[1:].strip()

        return text

    def _parse_chain_text(self, chain: list) -> str:
        parts = []
        for comp in chain:
            if isinstance(comp, Plain) and comp.text:
                parts.append(comp.text.strip())
        return " ".join(p for p in parts if p).strip()

    # ── 辅助方法 ──────────────────────────────────

    @staticmethod
    def _plain_text(event: AstrMessageEvent) -> str:
        return "".join(
            c.text for c in event.get_messages()
            if isinstance(c, Plain) and c.text
        )

    @staticmethod
    def _is_at_me(event: AstrMessageEvent) -> bool:
        self_id = str(event.get_self_id())
        for comp in event.get_messages():
            if isinstance(comp, At) and str(comp.qq) == self_id:
                return True
        return False

    @staticmethod
    def _has_reply(event: AstrMessageEvent) -> bool:
        for comp in event.get_messages():
            if isinstance(comp, Reply) and comp.chain:
                return True
        return False

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """去除 Markdown 及（篇幅、辞气）前缀。"""
        text = re.sub(r"\*{1,2}", "", text)
        text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^（[^）]+）\s*", "", text)
        return text
