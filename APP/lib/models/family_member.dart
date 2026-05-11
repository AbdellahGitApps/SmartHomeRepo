class FamilyMember {
  final int? id;
  final String? name;
  final String? role;
  final bool? hasFaceEmbedding;
  final String? createdAt;

  FamilyMember({
    this.id,
    this.name,
    this.role,
    this.hasFaceEmbedding,
    this.createdAt,
  });

  factory FamilyMember.fromJson(Map<String, dynamic> json) {
    return FamilyMember(
      id: json['id'],
      name: json['name'],
      role: json['role'],
      hasFaceEmbedding: json['has_face_embedding'],
      createdAt: json['created_at'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'role': role,
      'has_face_embedding': hasFaceEmbedding,
      'created_at': createdAt,
    };
  }
}