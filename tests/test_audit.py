import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from payment_processing_claim_audit.audit import audit, claims, evidence, GENERIC
from payment_processing_claim_audit.phrases import PAYMENTPROCESSING, NOPAYMENTPROCESSING
from payment_processing_claim_audit.__main__ import main

EXPECTED_YES = ('processes payments', 'process payments', 'processes a payment', 'process a payment', 'processes payment', 'process payment', 'payment processing support', 'supports payment processing', 'supports processing payments', 'supports processing a payment', 'payment processing feature', 'payment processing functionality', 'payment processing capability', 'payment processing capabilities', 'payment processing', 'processes payments with stripe', 'process payments with stripe', 'processes payments with paypal', 'process payments with paypal', 'processes payments with square', 'process payments with square', 'processes payments with braintree', 'process payments with braintree', 'processes payments with adyen', 'process payments with adyen', 'processes payments with razorpay', 'process payments with razorpay', 'processes payments with mollie', 'process payments with mollie', 'processes payments with checkout.com', 'process payments with checkout.com', 'charges credit cards', 'charge credit cards', 'charges a credit card', 'charge a credit card', 'charges cards', 'charge cards', 'refunds payments', 'refund payments', 'refunds a payment', 'refund a payment', 'captures payments', 'capture payments', 'accepts payments', 'accept payments', 'accepts card payments', 'accept card payments', 'processes card payments', 'process card payments', 'processes online payments')
EXPECTED_NO = ('does not process payments', 'never processes payments', 'does not process a payment', 'never processes a payment', 'does not process payment', 'never processes payment', 'no payment processing support', 'does not support payment processing', 'never supports payment processing', 'never supports processing payments', 'no payment processing feature', 'no payment processing functionality', 'no payment processing capability', 'does not process payments with stripe', 'never processes payments with stripe', 'does not process payments with paypal', 'never processes payments with paypal', 'does not charge credit cards', 'never charges credit cards', 'does not refund payments', 'never refunds payments', 'no payment processing', 'does not accept payments', 'never accepts payments')

class AuditTests(unittest.TestCase):
    def test_phrase_oracle(self):
        self.assertEqual(PAYMENTPROCESSING, EXPECTED_YES)
        self.assertEqual(NOPAYMENTPROCESSING, EXPECTED_NO)
        for phrase in EXPECTED_YES: self.assertEqual(claims(phrase), (True, False))
        for phrase in EXPECTED_NO: self.assertEqual(claims(phrase), (False, True))
    def test_routes(self):
        cases = []
        for prefix, methods in {'stripe.PaymentIntent':'create create_async capture capture_async confirm confirm_async', 'stripe.Charge':'create create_async capture capture_async', 'stripe.Refund':'create create_async', 'stripe.checkout.Session':'create create_async', 'braintree.Transaction':'sale refund submit_for_settlement void'}.items():
            cases += ['import '+prefix.split('.')[0]+'; '+prefix+'.'+m+'()' for m in methods.split()]
        cases += ['from stripe import PaymentIntent as P; P.create()', 'from braintree import Transaction as T; T.sale()']
        for chain, methods in {'transaction':'sale refund submit_for_settlement void', 'payments_api':'payments payments_details sessions'}.items():
            cases += ['x.'+chain+'.'+m+'()' for m in methods.split()]
        for chain, methods in {'payment_intents':'create create_async capture capture_async confirm confirm_async', 'charges':'create create_async capture capture_async', 'refunds':'create create_async'}.items():
            cases += ['import stripe; stripe.StripeClient(); x.'+chain+'.'+m+'()' for m in methods.split()]
        cases += ['from stripe import StripeClient as SC; SC(); x.refunds.create()']
        for group, names in {'orders':'OrdersCreateRequest OrdersCaptureRequest OrdersAuthorizeRequest', 'payments':'AuthorizationsCaptureRequest AuthorizationsVoidRequest CapturesRefundRequest'}.items():
            cases += ['from paypalcheckoutsdk.'+group+' import '+n+'; '+n+'(); x.execute()' for n in names.split()]
        cases += ['import paypalrestsdk; paypalrestsdk.Payment(); x.'+m+'()' for m in ('create','execute')]
        for constructor, chain, methods in [('square.Client','payments','create create_payment complete cancel'),('square.client.Client','refunds','refund_payment'),('Adyen.Adyen','modifications_api','capture_authorised_payment refund_captured_payment cancel_authorised_payment refund_or_cancel_payment cancel_authorised_payment_by_psp_reference'),('razorpay.Client','order','create'),('razorpay.Client','payment','capture refund'),('mollie.api.client.Client','payments','create delete'),('mollie.api.client.Client','refunds','create'),('mollie.api.client.Client','orders','create')]:
            cases += ['import '+constructor.split('.')[0]+'; '+constructor+'(); x.'+chain+'.'+m+'()' for m in methods.split()]
        cases += ['x.'+n+'()' for n in GENERIC | {'request_payment','capture_payment','refund_payment','void_payment'}]
        cases += ['from x import process_payment as p; p()']
        for code in cases:
            with self.subTest(code=code): self.assertTrue(evidence(code))
    def test_non_evidence(self):
        cases = ['import stripe', 'import stripe; stripe.StripeClient()', 'import square; square.Client()', 'import razorpay; razorpay.Client()', 'import mollie; mollie.api.client.Client()', 'import Adyen; Adyen.Adyen()', 'import braintree; braintree.BraintreeGateway()', 'x.execute()', 'x.payment_intents.create()', 'x.charges.create()', 'x.refunds.create()', 'x.payments.create()', 'x.order.create()', 'x.modifications_api.capture_authorised_payment()', 'import paypalrestsdk; paypalrestsdk.Payment()', 'import paypalrestsdk; paypalrestsdk.Payout(); x.create()', 'import requests; requests.post("https://api.stripe.com/v1/charges")', 'import stripe; stripe.api_key = "x"', 'import stripe; stripe.Webhook.construct_event()', 'def process_payment(): pass\nx.process_payment()', '"processes payments"', 'import subprocess; subprocess.run(["stripe"])', 'mindee.parse(InvoiceV4)', 'x.begin_analyze_document("prebuilt-layout")', 'veryfi.Client()', 'documentai.process_document()', 'textract.analyze_document()', 'eden.universal_ai()', 'llamaparse.parse()', 'nanonets.ocr(model_id="opaque")', 'docsumo.upload()', 'import stripe; stripe = x; stripe.PaymentIntent.create()', 'from stripe import PaymentIntent; with x as PaymentIntent: pass\nPaymentIntent.create()']
        for cls in ('SetupIntent','Subscription','PaymentLink','PaymentMethod','Customer','Invoice'):
            cases.append('import stripe; stripe.'+cls+'.create()')
        for cls in ('PaymentIntent','Charge'): cases.append('import stripe; stripe.'+cls+'.retrieve()')
        cases += ['from paypalcheckoutsdk.orders import OrdersGetRequest; OrdersGetRequest(); x.execute()']
        cases += ['import square; square.Client(); x.'+c+'.'+m+'()' for c,m in [('payments','list'),('orders','create'),('payouts','create'),('checkout','create_checkout')]]
        cases += ['import braintree; braintree.'+c+'.'+m+'()' for c,m in [('Transaction','find'),('Customer','create'),('PaymentMethod','create'),('Subscription','create')]]
        cases += ['x.payments_api.'+m+'()' for m in ('payment_methods','get_result_of_payment_session','update_authorised_amount')]
        cases += ['import razorpay; razorpay.Client(); x.'+c+'.'+m+'()' for c,m in [('order','fetch'),('payment','fetch'),('invoice','create'),('subscription','create')]]
        cases += ['import mollie; mollie.api.client.Client(); x.'+c+'.'+m+'()' for c,m in [('payments','get'),('methods','list'),('payment_links','create'),('customers','create')]]
        cases += ['x.get_payment_details()']
        for code in cases:
            with self.subTest(code=code): self.assertFalse(evidence(code))
    def test_documents_and_findings(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); readme=root/'README.md'; readme.write_text('processes payments')
            result=audit(root); self.assertEqual(result['findings'][0]['id'], 'documented-payment-processing-claim-false'); self.assertEqual(result['findings'][0]['severity'],'HIGH'); self.assertEqual(main(['audit',d]),2)
            (root/'tests').mkdir(); (root/'tests/test_x.py').write_text('x.charge_card()')
            self.assertEqual(audit(root)['findings'][0]['severity'],'MEDIUM'); self.assertEqual(main(['audit',d]),0); self.assertEqual(main(['audit',d,'--fail-on','medium']),2)
            (root/'app.py').write_text('x.charge_card()'); self.assertEqual(audit(root)['verdict'],'PASS')
            readme.write_text('does not process payments'); self.assertEqual(audit(root)['findings'][0]['id'],'documented-no-payment-processing-claim-false'); self.assertEqual(main(['audit',d]),2)
            (root/'app.py').unlink(); self.assertEqual(audit(root)['verdict'],'PASS')
            readme.write_text('```\nprocesses payments\n```'); self.assertEqual(audit(root)['verdict'],'PASS')
            readme.write_text('`processes payments`'); self.assertEqual(audit(root)['findings'][0]['severity'],'MEDIUM')
            readme.write_text('ordinary words'); self.assertEqual(audit(root)['verdict'],'PASS')
    def test_split_ignore_symlink_and_json(self):
        import os, subprocess, sys
        with tempfile.TemporaryDirectory() as d, tempfile.TemporaryDirectory() as outside:
            p=Path(d); (p/'README.md').write_text('processes payments'); (p/'a.py').write_text('import paypalrestsdk; paypalrestsdk.Payment()'); (p/'b.py').write_text('x.execute()')
            self.assertEqual(audit(p)['verdict'],'FAIL'); (p/'b.py').write_text('x.charge_card()'); self.assertEqual(audit(p)['verdict'],'PASS'); self.assertEqual(audit(p,['b.py'])['verdict'],'FAIL')
            (p/'b.py').unlink(); target=Path(outside)/'external.py'; target.write_text('x.charge_card()'); (p/'link.py').symlink_to(target); self.assertEqual(audit(p)['verdict'],'FAIL')
            env=dict(os.environ); env['PYTHONPATH']=str(Path(__file__).resolve().parents[1]/'src')
            r=subprocess.run([sys.executable,'-m','payment_processing_claim_audit','audit',d,'--json'],capture_output=True,text=True,env=env); self.assertEqual(r.returncode,2); result=json.loads(r.stdout); self.assertEqual(result['verdict'],'FAIL'); self.assertTrue(result['findings'][0]['message'])
    def test_version(self):
        with self.assertRaises(SystemExit) as e: main(['--version'])
        self.assertEqual(e.exception.code,0)

if __name__ == '__main__': unittest.main()
