//widgets/weather_background.dart
import 'dart:math';
import 'package:flutter/material.dart';

class WeatherBackground extends StatelessWidget {
  final bool isRaining;
  final bool isNight;
  final double rainDirection;
  final double sunAlt;

  const WeatherBackground({
    super.key,
    required this.isRaining,
    required this.isNight,
    required this.rainDirection,
    required this.sunAlt,
  });

  @override
  Widget build(BuildContext context) {
    final colors = isNight
        ? [const Color(0xFF0A0F1A), const Color(0xFF000000)]
        : isRaining
            ? [const Color(0xFF1E2A33), const Color(0xFF0F1A22)]
            : [const Color(0xFFFFF5C3), const Color(0xFFFFD37A)];

    return Stack(
      children: [
        Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: colors,
            ),
          ),
        ),

        if (isRaining) _buildRain(),
      ],
    );
  }

  Widget _buildRain() {
    final double angleRad = (-rainDirection) * pi / 180;

    return Transform.rotate(
      angle: angleRad,
      child: CustomPaint(
        painter: _RainPainter(),
        child: Container(),
      ),
    );
  }
}

class _RainPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..strokeWidth = 3
      ..color = Colors.white.withOpacity(0.25);

    final rnd = Random();

    for (int i = 0; i < 320; i++) {
      final x = rnd.nextDouble() * size.width;
      final y = rnd.nextDouble() * size.height;
      canvas.drawLine(Offset(x, y), Offset(x - 6, y + 20), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
