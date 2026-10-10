//widgets/compass_widget.dart
import 'package:flutter/material.dart';
import 'dart:math';

class CompassWidget extends StatelessWidget {
  final double rotation;

  const CompassWidget({super.key, required this.rotation});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 120,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 120,
            height: 120,
            child: Stack(
              alignment: Alignment.center,
              children: [
                Container(
                  width: 120,
                  height: 120,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(color: Colors.white70, width: 3),
                  ),
                ),

                Positioned(top: 4, child: _txt("N")),
                Positioned(bottom: 4, child: _txt("S")),
                Positioned(left: 4, child: _txt("W")),
                Positioned(right: 4, child: _txt("E")),

                // 사용자 위치
                const Icon(Icons.person_pin_circle,
                    color: Colors.white, size: 26),

                // 바늘 (CCW = -rotation 적용)
                Transform.rotate(
                  angle: -rotation * pi / 180,
                  child: Container(
                    width: 4,
                    height: 60,
                    decoration: BoxDecoration(
                      color: Colors.redAccent,
                      borderRadius: BorderRadius.circular(3),
                    ),
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 4),
          const Text(
            "👤 (사용자 기준: 북쪽)",
            style: TextStyle(color: Colors.white70, fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _txt(String s) => Text(
        s,
        style: const TextStyle(
            fontSize: 15, fontWeight: FontWeight.bold, color: Colors.white),
      );
}
