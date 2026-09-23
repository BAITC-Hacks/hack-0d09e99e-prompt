import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/providers.dart';
import '../data/repository.dart';
import '../theme/tokens.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _user = TextEditingController();
  final _pass = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _user.dispose();
    _pass.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await ref.read(authProvider.notifier).login(_user.text.trim(), _pass.text);
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _fill(String user, String pass) {
    _user.text = user;
    _pass.text = pass;
    _submit();
  }

  @override
  Widget build(BuildContext context) {
    final field = InputDecoration(
      filled: true,
      fillColor: Qc.card,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Qc.line)),
      enabledBorder:
          OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: Qc.line)),
    );
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 48, 24, 24),
          children: [
            Align(
              alignment: Alignment.centerLeft,
              child: Container(
                width: 56,
                height: 56,
                alignment: Alignment.center,
                decoration: BoxDecoration(color: Qc.primary, borderRadius: BorderRadius.circular(16)),
                child: const Text('Q', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 28)),
              ),
            ),
            const SizedBox(height: 20),
            const Text('Qor', style: TextStyle(fontSize: 32, fontWeight: FontWeight.w800, color: Qc.ink)),
            const SizedBox(height: 4),
            const Text('Согласование заказов поставщикам', style: TextStyle(color: Qc.inkSecondary, fontSize: 16)),
            const SizedBox(height: 32),
            TextField(
              controller: _user,
              autocorrect: false,
              textInputAction: TextInputAction.next,
              decoration: field.copyWith(labelText: 'Логин'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _pass,
              obscureText: true,
              textInputAction: TextInputAction.done,
              onSubmitted: (_) => _submit(),
              decoration: field.copyWith(labelText: 'Пароль'),
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: const TextStyle(color: Qc.critical)),
            ],
            const SizedBox(height: 20),
            FilledButton(
              onPressed: _busy ? null : _submit,
              child: _busy
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Text('Войти'),
            ),
            const SizedBox(height: 28),
            const Text('Демо-входы', style: TextStyle(fontWeight: FontWeight.w700, color: Qc.ink)),
            const SizedBox(height: 8),
            Wrap(spacing: 8, runSpacing: 8, children: [
              ActionChip(label: const Text('Руководитель · daniyar'), onPressed: () => _fill('daniyar', 'director')),
              ActionChip(label: const Text('Менеджер · aigerim'), onPressed: () => _fill('aigerim', 'buyer')),
            ]),
            const SizedBox(height: 16),
            Text('Сервер: ${ref.read(repositoryProvider).baseUrl}',
                style: const TextStyle(fontSize: 12, color: Qc.inkMuted)),
          ],
        ),
      ),
    );
  }
}
