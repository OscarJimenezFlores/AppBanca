import '../domain/gateways.dart';
import '../types/models.dart';
import 'api_client.dart';

class ApiBank implements AuthGateway, AccountGateway, TransferGateway, PaymentGateway, CardGateway, SecurityGateway, BranchGateway {
  ApiBank(this._api);

  final ApiClient _api;

  LoginResult _login(Map<String, dynamic> json) {
    return LoginResult(
      requiresOtp: json['requires_otp'] == true,
      accessToken: json['access_token'] as String?,
      refreshToken: json['refresh_token'] as String?,
      challengeToken: json['challenge_token'] as String?,
      expiresIn: json['expires_in'] as int?,
    );
  }

  @override
  Future<LoginResult> login(String identifier, String password) async {
    return _login(await _api.post('/api/v1/auth/login', {'identifier': identifier, 'password': password}));
  }

  @override
  Future<LoginResult> verifyOtp(String challengeToken, String code) async {
    return _login(await _api.post('/api/v1/auth/otp', {'challenge_token': challengeToken, 'code': code}));
  }

  @override
  Future<LoginResult> register(Map<String, String> body) async {
    return _login(await _api.post('/api/v1/auth/register', body));
  }

  @override
  Future<UserProfile> me() async {
    final json = await _api.get('/api/v1/me');
    return UserProfile(
      id: json['id'].toString(),
      fullName: json['full_name'].toString(),
      email: json['email'].toString(),
      phoneMasked: json['phone_masked'].toString(),
      dni: json['dni'].toString(),
      totpEnabled: json['totp_enabled'] == true,
    );
  }

  @override
  Future<void> logout(String refreshToken) {
    return _api.postEmpty('/api/v1/auth/logout', {'refresh_token': refreshToken});
  }

  @override
  Future<List<BankAccount>> accounts() async {
    final rows = await _api.getList('/api/v1/accounts');
    return rows.map((row) => _account(row as Map)).toList();
  }

  BankAccount _account(Map json) {
    return BankAccount(
      id: json['id'].toString(),
      productType: json['product_type'].toString(),
      productLabel: json['product_label'].toString(),
      alias: json['alias'].toString(),
      number: json['number'].toString(),
      numberMasked: json['number_masked'].toString(),
      cci: json['cci'].toString(),
      cciFormatted: json['cci_formatted'].toString(),
      availableBalance: json['available_balance'].toString(),
      status: json['status'].toString(),
    );
  }

  @override
  Future<List<Movement>> movements(String accountId) async {
    final json = await _api.get('/api/v1/accounts/$accountId/movements', query: {'page_size': 20});
    final items = json['items'] as List? ?? [];
    return items.map((row) {
      final item = row as Map;
      return Movement(
        id: item['id'].toString(),
        direction: item['direction'].toString(),
        amount: item['amount'].toString(),
        concept: item['concept'].toString(),
        counterpartyName: item['counterparty_name'].toString(),
        occurredAt: DateTime.parse(item['occurred_at'].toString()),
        operationCode: item['operation_code'].toString(),
      );
    }).toList();
  }

  @override
  Future<TransferReceipt> transfer(Map<String, dynamic> body) async {
    return _receipt(await _api.post('/api/v1/transfers', body));
  }

  @override
  Future<List<Beneficiary>> beneficiaries() async {
    final rows = await _api.getList('/api/v1/beneficiaries');
    return rows.map((row) {
      final item = row as Map;
      return Beneficiary(
        id: item['id'].toString(),
        alias: item['alias'].toString(),
        holderName: item['holder_name'].toString(),
        bankName: item['bank_name'].toString(),
        accountNumber: item['account_number']?.toString(),
        cci: item['cci']?.toString(),
      );
    }).toList();
  }

  @override
  Future<List<ServiceOffer>> services() async {
    final rows = await _api.getList('/api/v1/payments/services');
    return rows.map((row) {
      final item = row as Map;
      return ServiceOffer(
        code: item['code'].toString(),
        name: item['name'].toString(),
        category: item['category'].toString(),
        referenceLabel: item['reference_label'].toString(),
        referencePattern: item['reference_pattern'].toString(),
        maxAmount: item['max_amount'].toString(),
      );
    }).toList();
  }

  @override
  Future<TransferReceipt> pay(Map<String, dynamic> body) async {
    final json = await _api.post('/api/v1/payments', body);
    return TransferReceipt(
      operationCode: json['operation_code'].toString(),
      amount: json['amount'].toString(),
      commission: '0.00',
      status: 'pagada',
      destinationHolder: json['service_name'].toString(),
    );
  }

  TransferReceipt _receipt(Map<String, dynamic> json) {
    return TransferReceipt(
      operationCode: json['operation_code'].toString(),
      amount: json['amount'].toString(),
      commission: json['commission'].toString(),
      status: json['status'].toString(),
      destinationHolder: json['destination_holder'].toString(),
    );
  }

  @override
  Future<List<CardProduct>> cards() async {
    final rows = await _api.getList('/api/v1/cards');
    return rows.map((row) => _card(row as Map)).toList();
  }

  @override
  Future<CardProduct> setBlocked(String cardId, bool blocked) async {
    final path = blocked ? '/api/v1/cards/$cardId/block' : '/api/v1/cards/$cardId/unblock';
    return _card(await _api.post(path, {}));
  }

  CardProduct _card(Map json) {
    return CardProduct(
      id: json['id'].toString(),
      brand: json['brand'].toString(),
      panMasked: json['pan_masked'].toString(),
      holderName: json['holder_name'].toString(),
      expiry: json['expiry'].toString(),
      status: json['status'].toString(),
      accountAlias: json['account_alias']?.toString(),
      expiryYear: json['expiry_year'] as int,
      expiryMonth: json['expiry_month'] as int,
    );
  }

  @override
  Future<TotpSetup> setupTotp() async {
    final json = await _api.post('/api/v1/security/totp/setup', {});
    return TotpSetup(secret: json['secret'].toString(), otpauthUri: json['otpauth_uri'].toString());
  }

  @override
  Future<void> confirmTotp(String code) {
    return _api.postEmpty('/api/v1/security/totp/confirm', {'code': code});
  }

  @override
  Future<void> disableTotp(String password, String code) {
    return _api.postEmpty('/api/v1/security/totp/disable', {'password': password, 'code': code});
  }

  @override
  Future<List<BranchOffice>> branches({double? latitude, double? longitude}) async {
    final query = <String, dynamic>{};
    if (latitude != null && longitude != null) {
      query['latitude'] = latitude;
      query['longitude'] = longitude;
    }
    final rows = await _api.getList('/api/v1/branches', query: query);
    return rows.map((row) {
      final item = row as Map;
      return BranchOffice(
        id: item['id'].toString(),
        name: item['name'].toString(),
        kind: item['kind'].toString(),
        address: item['address'].toString(),
        district: item['district'].toString(),
        hours: item['hours'].toString(),
        latitude: (item['latitude'] as num).toDouble(),
        longitude: (item['longitude'] as num).toDouble(),
        distanceKm: item['distance_km'] == null ? null : (item['distance_km'] as num).toDouble(),
      );
    }).toList();
  }
}
