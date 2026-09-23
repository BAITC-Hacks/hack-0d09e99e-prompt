import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/format.dart';
import '../data/models.dart';
import '../data/providers.dart';
import '../data/repository.dart';
import '../theme/tokens.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key, required this.bundle, required this.line});

  final Bundle bundle;
  final SkuLine line;

  static Route<void> route(Bundle bundle, SkuLine line) =>
      MaterialPageRoute(builder: (_) => ChatScreen(bundle: bundle, line: line));

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _Msg {
  const _Msg(this.text, {required this.mine});
  final String text;
  final bool mine;
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  static const _suggestions = ['Почему так много?', 'Что если утвердить как есть?', 'Есть ли уже товар в пути?'];

  final _input = TextEditingController();
  final _scroll = ScrollController();
  final _messages = <_Msg>[];
  bool _thinking = false;

  @override
  void dispose() {
    _input.dispose();
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _send(String text) async {
    final q = text.trim();
    if (q.isEmpty || _thinking) return;
    _input.clear();
    setState(() {
      _messages.add(_Msg(q, mine: true));
      _thinking = true;
    });
    _toBottom();
    String answer;
    try {
      answer = await ref.read(repositoryProvider).ask(widget.line.code, q);
    } on ApiException catch (e) {
      answer = e.message;
    }
    if (!mounted) return;
    setState(() {
      _messages.add(_Msg(answer, mine: false));
      _thinking = false;
    });
    _toBottom();
  }

  void _toBottom() => WidgetsBinding.instance.addPostFrameCallback((_) {
        if (_scroll.hasClients) {
          _scroll.animateTo(_scroll.position.maxScrollExtent,
              duration: const Duration(milliseconds: 250), curve: Curves.easeOut);
        }
      });

  @override
  Widget build(BuildContext context) {
    final line = widget.line;
    return Scaffold(
      appBar: AppBar(
        title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Спросить почему', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
          Text('${line.article} · рек. ${fmtQty(line.recommended)} ${line.unit}',
              style: Qc.mono.copyWith(fontSize: 12, color: Qc.inkSecondary, fontWeight: FontWeight.w500)),
        ]),
      ),
      body: Column(children: [
        Expanded(
          child: ListView(
            controller: _scroll,
            padding: const EdgeInsets.all(16),
            children: [
              const _Bubble(
                _Msg('Отвечаю по цифрам расчёта: остатки, путь, сезонность, исключённые накладные. '
                    'Имена клиентов не использую.', mine: false),
              ),
              for (final m in _messages) _Bubble(m),
              if (_thinking)
                const Padding(
                  padding: EdgeInsets.only(top: 8),
                  child: Row(children: [
                    SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Qc.ai)),
                    SizedBox(width: 8),
                    Text('Считаю…', style: TextStyle(color: Qc.inkMuted)),
                  ]),
                ),
            ],
          ),
        ),
        if (_messages.isEmpty)
          SizedBox(
            height: 44,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              children: [
                for (final s in _suggestions)
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ActionChip(
                      label: Text(s),
                      backgroundColor: Qc.aiBg,
                      side: const BorderSide(color: Qc.aiBorder),
                      labelStyle: const TextStyle(color: Qc.ai, fontWeight: FontWeight.w600),
                      onPressed: () => _send(s),
                    ),
                  ),
              ],
            ),
          ),
        Container(
          decoration: const BoxDecoration(color: Qc.card, border: Border(top: BorderSide(color: Qc.line))),
          padding: const EdgeInsets.fromLTRB(12, 8, 8, 8),
          child: SafeArea(
            top: false,
            child: Row(children: [
              Expanded(
                child: TextField(
                  controller: _input,
                  textInputAction: TextInputAction.send,
                  onSubmitted: _send,
                  decoration: const InputDecoration(hintText: 'Спросить модель…', border: InputBorder.none),
                ),
              ),
              IconButton(
                tooltip: 'Голосом',
                icon: const Icon(Icons.graphic_eq, color: Qc.inkSecondary),
                onPressed: () => ScaffoldMessenger.of(context)
                    .showSnackBar(const SnackBar(content: Text('Голосовой ввод пока не поддерживается'))),
              ),
              IconButton.filled(
                icon: const Icon(Icons.arrow_upward),
                onPressed: () => _send(_input.text),
              ),
            ]),
          ),
        ),
      ]),
    );
  }
}

class _Bubble extends StatelessWidget {
  const _Bubble(this.msg);

  final _Msg msg;

  @override
  Widget build(BuildContext context) {
    return Align(
      alignment: msg.mine ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.82),
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        decoration: BoxDecoration(
          color: msg.mine ? Qc.accent : Qc.card,
          border: msg.mine ? null : Border.all(color: Qc.line),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: Radius.circular(msg.mine ? 16 : 4),
            bottomRight: Radius.circular(msg.mine ? 4 : 16),
          ),
        ),
        child: Text(msg.text, style: TextStyle(color: msg.mine ? Colors.white : Qc.ink, height: 1.4)),
      ),
    );
  }
}
