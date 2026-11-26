import os, sqlite3, uuid, io, secrets, hmac
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, send_file, abort, jsonify
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit

BASE=Path(__file__).resolve().parent
app=Flask(__name__)
app.config['MAX_CONTENT_LENGTH']=12000
DB=BASE/'orders.sqlite3'
PRICE_CENTS=699

def db():
    conn=sqlite3.connect(DB)
    conn.row_factory=sqlite3.Row
    return conn

def init():
    with db() as c:
        c.execute('''CREATE TABLE IF NOT EXISTS orders (id TEXT PRIMARY KEY, token TEXT UNIQUE NOT NULL, child TEXT NOT NULL, age TEXT, accomplishment TEXT, wish TEXT, recipient TEXT NOT NULL, email TEXT NOT NULL, postal_address TEXT, paid INTEGER NOT NULL DEFAULT 0, created TEXT NOT NULL, session_id TEXT)''')
init()

def field(key, limit=120):
    return ' '.join(request.form.get(key,'').strip().split())[:limit]

def pdf_for(order, sample=False):
    buf=io.BytesIO(); p=canvas.Canvas(buf,pagesize=(612,792)); p.setTitle('A Magical Letter from Santa Claus')
    red=HexColor('#9b2530'); green=HexColor('#174c3c'); gold=HexColor('#b88b3f')
    p.setFillColor(HexColor('#fffaf0')); p.rect(0,0,612,792,fill=1,stroke=0)
    for inset in [24,30]:
        p.setStrokeColor(gold if inset==24 else green);p.setLineWidth(2 if inset==24 else .7);p.roundRect(inset,inset,612-2*inset,792-2*inset,12,stroke=1,fill=0)
    # Festive ornament corners
    for x,y in [(54,736),(558,736),(54,56),(558,56)]:
        p.setFillColor(red);p.circle(x,y,8,fill=1,stroke=0)
        p.setFillColor(green);p.circle(x+12,y+7,5,fill=1,stroke=0)
        p.setFillColor(gold);p.circle(x-9,y+10,3,fill=1,stroke=0)
    p.setFillColor(green);p.setFont('Times-Bold',25);p.drawCentredString(306,711,'THE NORTH POLE POST OFFICE')
    p.setFillColor(red);p.setFont('Times-Italic',15);p.drawCentredString(306,687,'Official Correspondence from Santa Claus')
    p.setStrokeColor(gold);p.line(95,674,517,674)
    p.setFillColor(green);p.setFont('Times-Bold',11);p.drawString(66,648,'NORTH POLE  •  CHRISTMAS EXPRESS')
    p.setFillColor(red);p.drawRightString(546,648,'December 2026')
    y=613
    def paragraph(txt, size=13, leading=21):
        nonlocal y
        p.setFillColor(HexColor('#283b34'));p.setFont('Times-Roman',size)
        for line in simpleSplit(txt,'Times-Roman',size,475):
            p.drawString(69,y,line);y-=leading
        y-=13
    p.setFillColor(red);p.setFont('Times-Bold',17);p.drawString(69,y,'Dear '+order['child']+',');y-=37
    paragraph('Ho, ho, ho! What a wonderful surprise to write to you from my snowy workshop at the North Pole! The elves have been busy preparing for Christmas, and your name brought a great big smile to my face.')
    if order['accomplishment']:
        paragraph('I heard something especially wonderful about you: '+order['accomplishment'].rstrip('. ') + '. You should be very proud of yourself!')
    else:
        paragraph('I hope you know how special you are. Every kind word and thoughtful deed helps make the world a little brighter.')
    if order['wish']:
        paragraph('The elves told me you have been dreaming about '+order['wish'].rstrip('. ')+'. They love hearing about your Christmas wishes!')
    paragraph('Remember, the greatest Christmas magic is found in kindness, laughter, and time spent with people who love you. Keep that wonderful sparkle in your heart!')
    if y<185: y=185
    p.setFillColor(green);p.setFont('Times-Italic',15);p.drawString(70,y-5,'With warmest Christmas wishes,')
    p.setFillColor(red);p.setFont('Times-BoldItalic',26);p.drawString(70,y-43,'Santa Claus')
    p.setFillColor(gold);p.setFont('Times-Bold',10);p.drawString(70,y-65,'NORTH POLE • OFFICIAL SANTA MAIL')
    # small elf-inspired decorative hats, stars and gifts (original vector art)
    for x in (440,477,514):
        p.setFillColor(green);path=p.beginPath();path.moveTo(x-12,115);path.lineTo(x+2,145);path.lineTo(x+13,115);path.close();p.drawPath(path,fill=1,stroke=0)
        p.setFillColor(red);p.circle(x+2,146,4,fill=1,stroke=0)
        p.setFillColor(HexColor('#f4c99b'));p.circle(x,107,11,fill=1,stroke=0)
        p.setFillColor(green);p.circle(x-4,109,1,fill=1,stroke=0);p.circle(x+4,109,1,fill=1,stroke=0)
    p.setStrokeColor(gold);p.line(69,88,543,88)
    p.setFont('Times-Italic',10);p.setFillColor(green);p.drawCentredString(306,69,'Hand-delivered by Christmas magic • Made especially for you')
    if sample:
        p.saveState();p.translate(306,400);p.rotate(35);p.setFillColor(HexColor('#d4aaa8'));p.setFont('Helvetica-Bold',65);p.drawCentredString(0,0,'SAMPLE');p.restoreState()
    p.showPage();p.save();buf.seek(0);return buf

@app.get('/')
def home(): return render_template('index.html', price='6.99', payments=bool(os.environ.get('STRIPE_SECRET_KEY')))

@app.post('/order')
def order():
    child=field('child',55);recipient=field('recipient',100);email=field('email',180)
    if not child or not recipient or '@' not in email or len(email)<5: return 'Please enter the child name, purchaser name, and valid email.',400
    oid=uuid.uuid4().hex; token=secrets.token_urlsafe(32)
    data=(oid,token,child,field('age',3),field('accomplishment',180),field('wish',120),recipient,email,field('address',250),datetime.now(timezone.utc).isoformat())
    with db() as c:c.execute('INSERT INTO orders(id,token,child,age,accomplishment,wish,recipient,email,postal_address,created) VALUES (?,?,?,?,?,?,?,?,?,?)',data)
    if request.form.get('sample')=='yes':return redirect(url_for('preview',token=token))
    key=os.environ.get('STRIPE_SECRET_KEY');domain=os.environ.get('PUBLIC_BASE_URL','').rstrip('/')
    if not key or not domain:return 'Checkout is not configured. Set STRIPE_SECRET_KEY and PUBLIC_BASE_URL. You can still use the sample preview.',503
    try:
        import stripe
        stripe.api_key=key
        session=stripe.checkout.Session.create(mode='payment',customer_email=email,client_reference_id=oid,
            line_items=[{'price_data':{'currency':'usd','product_data':{'name':'Personalized Santa Letter PDF'},'unit_amount':PRICE_CENTS},'quantity':1}],
            success_url=domain+'/success?session_id={CHECKOUT_SESSION_ID}',cancel_url=domain+'/',metadata={'order_id':oid})
        with db() as c:c.execute('UPDATE orders SET session_id=? WHERE id=?',(session.id,oid))
        return redirect(session.url,code=303)
    except Exception:
        app.logger.exception('Stripe checkout error')
        return 'Payment service unavailable. Please try again later.',503

def find_order(token):
    with db() as c:return c.execute('SELECT * FROM orders WHERE token=?',(token,)).fetchone()

@app.get('/preview/<token>')
def preview(token):
    o=find_order(token)
    if not o:abort(404)
    return send_file(pdf_for(o,True),mimetype='application/pdf',download_name='Santa_sample.pdf')

@app.get('/download/<token>')
def download(token):
    o=find_order(token)
    if not o:abort(404)
    if not o['paid']:abort(403)
    return send_file(pdf_for(o),mimetype='application/pdf',as_attachment=True,download_name='Santa_Letter.pdf')

@app.get('/success')
def success():
    sid=request.args.get('session_id','')
    if not sid:abort(400)
    with db() as c:o=c.execute('SELECT * FROM orders WHERE session_id=?',(sid,)).fetchone()
    if not o:abort(404)
    # Verify directly with Stripe as well as webhook to handle webhook delay
    if not o['paid'] and os.environ.get('STRIPE_SECRET_KEY'):
        import stripe
        stripe.api_key=os.environ['STRIPE_SECRET_KEY']domain='https://santas-magical-mail-vhrj.onrender.com'
        try:
            s=stripe.checkout.Session.retrieve(sid)
            if s.payment_status=='paid' and s.client_reference_id==o['id']:
                with db() as c:c.execute('UPDATE orders SET paid=1 WHERE id=?',(o['id'],))
                o=find_order(o['token'])
        except Exception:app.logger.exception('Stripe verification error')
    return render_template('success.html',paid=bool(o['paid']),link=url_for('download',token=o['token']))

@app.post('/stripe-webhook')
def webhook():
    import stripe
    secret=os.environ.get('STRIPE_WEBHOOK_SECRET')
    if not secret:return 'Webhook not configured',503
    try:event=stripe.Webhook.construct_event(request.data,request.headers.get('Stripe-Signature',''),secret)
    except (ValueError,stripe.error.SignatureVerificationError):return 'Invalid signature',400
    if event['type']=='checkout.session.completed':
        s=event['data']['object']
        if s.get('payment_status')=='paid':
            with db() as c:c.execute('UPDATE orders SET paid=1 WHERE id=? AND session_id=?',(s.get('client_reference_id'),s.get('id')))
    return jsonify(ok=True)

@app.get('/health')
def health():return jsonify(status='ok')

if __name__=='__main__':app.run(host='127.0.0.1',port=int(os.environ.get('PORT',5000)),debug=False)
