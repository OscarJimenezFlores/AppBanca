import '../types/models.dart';

abstract class AuthGateway {
  Future<LoginResult> login(String identifier, String password);
  Future<LoginResult> verifyOtp(String challengeToken, String code);
  Future<LoginResult> register(Map<String, String> body);
  Future<UserProfile> me();
  Future<void> logout(String refreshToken);
}

abstract class AccountGateway {
  Future<List<BankAccount>> accounts();
  Future<List<Movement>> movements(String accountId);
}

abstract class TransferGateway {
  Future<TransferReceipt> transfer(Map<String, dynamic> body);
  Future<List<Beneficiary>> beneficiaries();
}

abstract class PaymentGateway {
  Future<List<ServiceOffer>> services();
  Future<TransferReceipt> pay(Map<String, dynamic> body);
}

abstract class CardGateway {
  Future<List<CardProduct>> cards();
  Future<CardProduct> setBlocked(String cardId, bool blocked);
}

abstract class SecurityGateway {
  Future<TotpSetup> setupTotp();
  Future<void> confirmTotp(String code);
  Future<void> disableTotp(String password, String code);
}

abstract class BranchGateway {
  Future<List<BranchOffice>> branches({double? latitude, double? longitude});
}
