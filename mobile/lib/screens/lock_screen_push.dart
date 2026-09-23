import 'dart:ui';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../data/format.dart';
import '../data/models.dart';
import '../data/providers.dart';
import '../theme/tokens.dart';

/// Lock-screen mock for the jury demo. Real pushes come with firebase_messaging.
class LockScreenPush extends ConsumerWidget {
  const LockScreenPush({super.key, required this.bundle});

  final Bundle bundle;

  static Route<void> route(Bundle bundle) => PageRouteBuilder(
        pageBuilder: (_, _, _) => LockScreenPush(bundle: bundle),
        transitionsBuilder: (_, a, _, child) => FadeTransition(opacity: a, child: child),
      );

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final now = DateTime.now();
    final sentBy = ref.watch(orderProvider).value?.sentBy;

    return Scaffold(
      backgroundColor: Colors.black,
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [Color(0xFF0B1B3F), Color(0xFF1E3A8A), Color(0xFF312E81)],
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: Column(children: [
              const SizedBox(height: 24),
              const Icon(Icons.lock, color: Colors.white70, size: 20),
              const SizedBox(height: 8),
              Text(ruDate(now), style: const TextStyle(color: Colors.white70, fontSize: 17, fontWeight: FontWeight.w500)),
              Text(hhmm(now),
                  style: const TextStyle(color: Colors.white, fontSize: 84, fontWeight: FontWeight.w300, height: 1.05)),
              const SizedBox(height: 28),
              GestureDetector(
                onTap: () {
                  ref.read(urgencyFilterProvider.notifier).set(null);
                  ref.read(tabProvider.notifier).go(1);
                  Navigator.of(context).popUntil((r) => r.isFirst);
                },
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(22),
                  child: BackdropFilter(
                    filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
                    child: Container(
                      padding: const EdgeInsets.all(14),
                      color: Colors.white.withValues(alpha: 0.78),
                      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Container(
                          width: 38,
                          height: 38,
                          alignment: Alignment.center,
                          decoration: BoxDecoration(color: Qc.primary, borderRadius: BorderRadius.circular(9)),
                          child: const Text('Q',
                              style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800, fontSize: 18)),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                            const Row(children: [
                              Text('Qor', style: TextStyle(fontWeight: FontWeight.w700, color: Qc.ink)),
                              Spacer(),
                              Text('сейчас', style: TextStyle(fontSize: 13, color: Qc.inkSecondary)),
                            ]),
                            const SizedBox(height: 2),
                            Text('Заказ ${bundle.supplier} ждёт утверждения',
                                style: const TextStyle(fontWeight: FontWeight.w600, color: Qc.ink)),
                            Text(
                              '${fmtQty(bundle.lines.length)} позиций · ${fmtQty(bundle.count(Urgency.critical))} критично${sentBy != null ? ' · от $sentBy' : ''}',
                              style: const TextStyle(color: Qc.ink, height: 1.3),
                            ),
                          ]),
                        ),
                      ]),
                    ),
                  ),
                ),
              ),
              const Spacer(),
              const Text('Нажмите на уведомление', style: TextStyle(color: Colors.white54)),
              const SizedBox(height: 12),
              Container(
                width: 134,
                height: 5,
                decoration: BoxDecoration(color: Colors.white70, borderRadius: BorderRadius.circular(3)),
              ),
              const SizedBox(height: 8),
            ]),
          ),
        ),
      ),
    );
  }
}
