class ApiException implements Exception {
  ApiException({required this.code, required this.message, this.status, this.details = const []});

  final String code;
  final String message;
  final int? status;
  final List<String> details;

  @override
  String toString() => message;
}

class LoginResult {
  const LoginResult({
    required this.requiresOtp,
    this.accessToken,
    this.refreshToken,
    this.challengeToken,
    this.expiresIn,
  });

  final bool requiresOtp;
  final String? accessToken;
  final String? refreshToken;
  final String? challengeToken;
  final int? expiresIn;
}

class UserProfile {
  const UserProfile({
    required this.id,
    required this.fullName,
    required this.email,
    required this.phoneMasked,
    required this.dni,
    required this.totpEnabled,
  });

  final String id;
  final String fullName;
  final String email;
  final String phoneMasked;
  final String dni;
  final bool totpEnabled;

  String get firstName => fullName.split(' ').first;
}

class BankAccount {
  const BankAccount({
    required this.id,
    required this.productType,
    required this.productLabel,
    required this.alias,
    required this.number,
    required this.numberMasked,
    required this.cci,
    required this.cciFormatted,
    required this.availableBalance,
    required this.status,
  });

  final String id;
  final String productType;
  final String productLabel;
  final String alias;
  final String number;
  final String numberMasked;
  final String cci;
  final String cciFormatted;
  final String availableBalance;
  final String status;

  bool get canDebit => productType != 'cts' && status == 'active';
}

class Movement {
  const Movement({
    required this.id,
    required this.direction,
    required this.amount,
    required this.concept,
    required this.counterpartyName,
    required this.occurredAt,
    required this.operationCode,
  });

  final String id;
  final String direction;
  final String amount;
  final String concept;
  final String counterpartyName;
  final DateTime occurredAt;
  final String operationCode;
}

class TransferReceipt {
  const TransferReceipt({
    required this.operationCode,
    required this.amount,
    required this.commission,
    required this.status,
    required this.destinationHolder,
  });

  final String operationCode;
  final String amount;
  final String commission;
  final String status;
  final String destinationHolder;
}

class ServiceOffer {
  const ServiceOffer({
    required this.code,
    required this.name,
    required this.category,
    required this.referenceLabel,
    required this.referencePattern,
    required this.maxAmount,
  });

  final String code;
  final String name;
  final String category;
  final String referenceLabel;
  final String referencePattern;
  final String maxAmount;
}

class CardProduct {
  const CardProduct({
    required this.id,
    required this.brand,
    required this.panMasked,
    required this.holderName,
    required this.expiry,
    required this.status,
    required this.accountAlias,
    required this.expiryYear,
    required this.expiryMonth,
  });

  final String id;
  final String brand;
  final String panMasked;
  final String holderName;
  final String expiry;
  final String status;
  final String? accountAlias;
  final int expiryYear;
  final int expiryMonth;

  bool get expired {
    final now = DateTime.now().toUtc().add(const Duration(hours: -5));
    return expiryYear < now.year || (expiryYear == now.year && expiryMonth < now.month);
  }
}

class BranchOffice {
  const BranchOffice({
    required this.id,
    required this.name,
    required this.kind,
    required this.address,
    required this.district,
    required this.hours,
    required this.latitude,
    required this.longitude,
    this.distanceKm,
  });

  final String id;
  final String name;
  final String kind;
  final String address;
  final String district;
  final String hours;
  final double latitude;
  final double longitude;
  final double? distanceKm;
}

class Beneficiary {
  const Beneficiary({
    required this.id,
    required this.alias,
    required this.holderName,
    required this.bankName,
    this.accountNumber,
    this.cci,
  });

  final String id;
  final String alias;
  final String holderName;
  final String bankName;
  final String? accountNumber;
  final String? cci;
}

class TotpSetup {
  const TotpSetup({required this.secret, required this.otpauthUri});

  final String secret;
  final String otpauthUri;
}
