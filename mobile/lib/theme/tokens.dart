import 'package:flutter/material.dart';

/// Design tokens shared with the web workspace (see ../tailwind.config.ts).
abstract final class Qc {
  static const canvas = Color(0xFFF5F7FA);
  static const card = Color(0xFFFFFFFF);
  static const primary = Color(0xFF004AC6);
  static const accent = Color(0xFF2563EB);
  static const primaryFixed = Color(0xFFDBE1FF);

  static const ink = Color(0xFF0F172A);
  static const inkSecondary = Color(0xFF475569);
  static const inkMuted = Color(0xFF94A3B8);
  static const line = Color(0xFFE2E8F0);
  static const surfaceLow = Color(0xFFEFF4FF);

  static const ai = Color(0xFF6366F1);
  static const aiBg = Color(0xFFEEF2FF);
  static const aiBorder = Color(0xFFC7D2FE);

  static const safe = Color(0xFF10B981);
  static const safeBg = Color(0xFFECFDF5);
  static const safeBorder = Color(0xFFA7F3D0);
  static const warning = Color(0xFFF59E0B);
  static const warningBg = Color(0xFFFFFBEB);
  static const warningBorder = Color(0xFFFDE68A);
  static const critical = Color(0xFFEF4444);
  static const criticalBg = Color(0xFFFEF2F2);
  static const criticalBorder = Color(0xFFFECACA);
  static const anomaly = Color(0xFFEA580C);
  static const anomalyBg = Color(0xFFFFF7ED);
  static const anomalyBorder = Color(0xFFFED7AA);

  static const radius = 16.0;

  static const mono = TextStyle(
    fontFamily: 'monospace',
    fontFamilyFallback: ['Menlo', 'Courier'],
    fontWeight: FontWeight.w600,
  );
}
