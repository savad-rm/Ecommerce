from django.shortcuts import render,redirect,reverse
from . import forms,models
from django.http import HttpResponseRedirect,HttpResponse
from django.core.mail import send_mail
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib import messages
from django.conf import settings
import razorpay

from django.utils.crypto import get_random_string
import json

def home_view(request):
    products=models.Product.objects.all()
    cart = request.session.get('cart', {})
    cart_items = list(cart.values())
    if cart_items:
        product_count_in_cart = len(cart_items)
    else:
        product_count_in_cart=0
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return render(request,'ecom/index.html',{'products':products,'product_count_in_cart':product_count_in_cart})
    
#for showing login button for admin
def adminclick_view(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect('afterlogin')
    return HttpResponseRedirect('adminlogin')

def customer_signup_view(request):
    userForm=forms.CustomerUserForm()
    customerForm=forms.CustomerForm()
    mydict={'userForm':userForm,'customerForm':customerForm}
    if request.method=='POST':
        userForm=forms.CustomerUserForm(request.POST)
        customerForm=forms.CustomerForm(request.POST,request.FILES)
        if userForm.is_valid() and customerForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            customer=customerForm.save(commit=False)
            customer.user=user
            customer.save()
            my_customer_group = Group.objects.get_or_create(name='CUSTOMER')
            my_customer_group[0].user_set.add(user)
        return HttpResponseRedirect('customerlogin')
    return render(request,'ecom/customersignup.html',context=mydict)

#-----------for checking user iscustomer
def is_customer(user):
    return user.groups.filter(name='CUSTOMER').exists()



#---------AFTER ENTERING CREDENTIALS WE CHECK WHETHER USERNAME AND PASSWORD IS OF ADMIN,CUSTOMER
def afterlogin_view(request):
    if is_customer(request.user):
        return redirect('customer-home')
    else:
        return redirect('admin-dashboard')

# @login_required(login_url='adminlogin')
# def logout_view(request):
    
#     products=models.Product.objects.all()
#     cart=request.session.get('cart', {})
#     product_count_in_cart = len(cart)
#     # redirect = HttpResponseRedirect('',{'products':products,'product_count_in_cart':product_count_in_cart})
#     # return redirect
#     return render(request,'ecom/logout.html',{'products':products,'product_count_in_cart':product_count_in_cart})
#     # return render(request,'ecom/index.html',{'products':products,'product_count_in_cart':product_count_in_cart})

#---------------------------------------------------------------------------------
#------------------------ ADMIN RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------
@login_required(login_url='adminlogin')
def admin_dashboard_view(request):
    # for cards on dashboard
    # customercount=models.Customer.objects.all().count()
    productcount=models.Product.objects.all().count()
    ordercount=models.Orders.objects.all().count()

    # for recent order tables
    orders=models.Orders.objects.all()
    ordered_products=[]
    ordered_bys=[]
    for order in orders:
        ordered_product=models.Product.objects.all().filter(id=order.product.id)
        # ordered_by=models.Customer.objects.all().filter(id = order.customer.id)
        ordered_products.append(ordered_product)
        # ordered_bys.append(ordered_by)

    mydict={
    # 'customercount':customercount,
    'productcount':productcount,
    'ordercount':ordercount,
    'data':zip(ordered_products,orders),
    # ,ordered_bys
    }
    return render(request,'ecom/admin_dashboard.html',context=mydict)

# admin view customer table
@login_required(login_url='adminlogin')
def view_customer_view(request):
    customers=models.Customer.objects.all()
    return render(request,'ecom/view_customer.html',{'customers':customers})

# admin delete customer
@login_required(login_url='adminlogin')
def delete_customer_view(request,pk):
    customer=models.Customer.objects.get(id=pk)
    user=models.User.objects.get(id=customer.user_id)
    user.delete()
    customer.delete()
    return redirect('view-customer')

@login_required(login_url='adminlogin')
def update_customer_view(request,pk):
    customer=models.Customer.objects.get(id=pk)
    user=models.User.objects.get(id=customer.user_id)
    userForm=forms.CustomerUserForm(instance=user)
    customerForm=forms.CustomerForm(request.FILES,instance=customer)
    mydict={'userForm':userForm,'customerForm':customerForm}
    if request.method=='POST':
        userForm=forms.CustomerUserForm(request.POST,instance=user)
        customerForm=forms.CustomerForm(request.POST,instance=customer)
        if userForm.is_valid() and customerForm.is_valid():
            user=userForm.save()
            user.set_password(user.password)
            user.save()
            customerForm.save()
            return redirect('view-customer')
    return render(request,'ecom/admin_update_customer.html',context=mydict)

# admin view the product
@login_required(login_url='adminlogin')
def admin_products_view(request):
    products=models.Product.objects.all()
    return render(request,'ecom/admin_products.html',{'products':products})


# admin add product by clicking on floating button
@login_required(login_url='adminlogin')
def admin_add_product_view(request):
    productForm=forms.ProductForm()
    if request.method=='POST':
        productForm=forms.ProductForm(request.POST, request.FILES)
        if productForm.is_valid():
            productForm.save()
        return HttpResponseRedirect('admin-products')
    return render(request,'ecom/admin_add_products.html',{'productForm':productForm})

@login_required(login_url='adminlogin')
def delete_product_view(request,pk):
    product=models.Product.objects.get(id=pk)
    product.delete()
    return redirect('admin-products')


@login_required(login_url='adminlogin')
def update_product_view(request,pk):
    product=models.Product.objects.get(id=pk)
    productForm=forms.ProductForm(instance=product)
    if request.method=='POST':
        productForm=forms.ProductForm(request.POST,request.FILES,instance=product)
        if productForm.is_valid():
            productForm.save()
            return redirect('admin-products')
    return render(request,'ecom/admin_update_product.html',{'productForm':productForm})


@login_required(login_url='adminlogin')
def admin_view_booking_view(request):
    orders=models.Orders.objects.all()
    ordered_products=[]
    ordered_bys=[]
    for order in orders:
        ordered_product=models.Product.objects.all().filter(id=order.product.id)
        ordered_by=models.Customer.objects.all().filter(id = order.customer.id)
        ordered_products.append(ordered_product)
        ordered_bys.append(ordered_by)
    return render(request,'ecom/admin_view_booking.html',{'data':zip(ordered_products,ordered_bys,orders)})


@login_required(login_url='adminlogin')
def delete_order_view(request,pk):
    order=models.Orders.objects.get(id=pk)
    order.delete()
    return redirect('admin-view-booking')

# for changing status of order (pending,delivered...)
@login_required(login_url='adminlogin')
def update_order_view(request,pk):
    order=models.Orders.objects.get(id=pk)
    orderForm=forms.OrderForm(instance=order)
    if request.method=='POST':
        orderForm=forms.OrderForm(request.POST,instance=order)
        if orderForm.is_valid():
            orderForm.save()
            return redirect('admin-view-booking')
    return render(request,'ecom/update_order.html',{'orderForm':orderForm})


# admin view the feedback
@login_required(login_url='adminlogin')
def view_feedback_view(request):
    feedbacks=models.Feedback.objects.all().order_by('-id')
    return render(request,'ecom/view_feedback.html',{'feedbacks':feedbacks})



#---------------------------------------------------------------------------------
#------------------------ PUBLIC CUSTOMER RELATED VIEWS START ---------------------
#---------------------------------------------------------------------------------
# any one can add product to cart, no need of signin
# def add_to_cart_view(request,pk):
#     products=models.Product.objects.all()

#     #for cart counter, fetching products ids added by customer from cookies
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         # counter=product_ids.split('|')
#         counter=len(product_ids)
#         # product_count_in_cart=len(set(counter))
#         product_count_in_cart=counter
#         # print(product_ids)
#     else:
#         product_count_in_cart=1

#     response = render(request, 'ecom/index.html',{'products':products,'product_count_in_cart':product_count_in_cart})

#     #adding product id to cookies
#     if 'product_ids' in request.COOKIES:
#         product_ids = request.COOKIES['product_ids']
#         if product_ids=="":
#             product_ids=str(pk)
#         else:
#             product_ids=product_ids+"|"+str(pk)
#         response.set_cookie('product_ids', product_ids)
#     else:
#         response.set_cookie('product_ids', pk)

#     product=models.Product.objects.get(id=pk)
#     messages.info(request, product.name + ' added to cart successfully!')

#     return response


def add_to_cart_view(request, pk):
    products = models.Product.objects.all()
    cartproduct = models.Product.objects.get(id=pk)
    if 'cart' not in request.session:
        request.session['cart'] = {}
    if str(cartproduct.id) in request.session['cart']:
        request.session['cart'][str(cartproduct.id)]['quantity'] += 1
    else:
        request.session['cart'][str(cartproduct.id)] = {
            'id': str(cartproduct.id),
            'name': cartproduct.name,
            'price': str(cartproduct.price),
            'quantity': 1,
        }
    request.session.modified = True  
    product_count_in_cart = len(request.session['cart'])
    notification_message = f"{cartproduct.name} added to cart Successfully!"
    notification_type = 'success'  # Other options: 'info', 'warning', 'error'
    extra_options = {'timeOut': 3000}  # Additional options, adjust as needed
    return render(request, 'ecom/index.html', {
        'products': products,
        'product_count_in_cart': product_count_in_cart,
        'notification_message': notification_message,
        'notification_type': notification_type,
        'extra_options': extra_options,
    })

    # response = render(request, 'ecom/index.html', {'products': products,'product_count_in_cart': product_count_in_cart})
    
    # return response
    # Save cart in cookies
    # response.set_cookie('cart', json.dumps(cart))


def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = list(cart.values())
    products=None
    if cart_items:
        products= models.Product.objects.filter(id__in=[item['id'] for item in cart_items])    
    total_price = sum(float(item['price']) * item['quantity'] for item in cart_items)
    product_count_in_cart = len(cart_items)
    return render(request, 'ecom/cart.html', {'products': products, 'total': total_price,'product_count_in_cart': product_count_in_cart})

def remove_from_cart_view(request, pk):
    product = models.Product.objects.get(id=pk)
    if 'cart' not in request.session:
        request.session['cart'] = {}
    if str(product.id) in request.session['cart']:
        del request.session['cart'][str(product.id)]
        request.session.modified = True
        cart=request.session['cart']
        cartproducts = list(cart.values())
        products = models.Product.objects.filter(id__in=[item['id'] for item in cartproducts.values()])
        total = sum(float(item['price']) * item['quantity'] for item in cartproducts.values())
        product_count_in_cart = len(cartproducts)        
        response = render(request, 'ecom/cart.html', {'products': products, 'total': total, 'product_count_in_cart': product_count_in_cart})
        return response

def send_feedback_view(request):
    feedbackForm=forms.FeedbackForm()
    if request.method == 'POST':
        feedbackForm = forms.FeedbackForm(request.POST)
        if feedbackForm.is_valid():
            feedbackForm.save()
            return render(request, 'ecom/feedback_sent.html')
    return render(request, 'ecom/send_feedback.html', {'feedbackForm':feedbackForm})


#---------------------------------------------------------------------------------
#------------------------ CUSTOMER RELATED VIEWS START ------------------------------
#---------------------------------------------------------------------------------

def customer_home_view(request):
    products=models.Product.objects.all()
    cart = request.session.get('cart', {})
    cart_items = list(cart.values())
    if cart_items:
        product_count_in_cart = len(cart_items)
    else:
        product_count_in_cart=0
    return render(request,'ecom/customer_home.html',{'products':products,'product_count_in_cart':product_count_in_cart})

def customer_address_view(request):
    # this is for checking whether product is present in cart or not
    # if there is no product in cart we will not show address form
    product_in_cart=False
    cart = request.session.get('cart', {})
    cart_items = list(cart.values())
    if cart_items:
        product_in_cart=True
    #for counter in cart
    cart = request.session.get('cart', {})
    cart_items = list(cart.values())
    if cart_items:
        product_count_in_cart = len(cart_items)
    else:
        product_count_in_cart=0

    addressForm = forms.AddressForm()
    if request.method == 'POST':
        addressForm = forms.AddressForm(request.POST)
        if addressForm.is_valid():
            # here we are taking address, email, mobile at time of order placement
            # we are not taking it from customer account table because
            # these thing can be changes
            # email = addressForm.cleaned_data['Email']
            name=addressForm.cleaned_data['Name']   
            mobile=addressForm.cleaned_data['Mobile']
            # address = addressForm.cleaned_data['Address']
            #for showing total price on payment page.....accessing id from cookies then fetching  price of product from db
            total=0
            cart = request.session.get('cart', {})
            cart_items = list(cart.values())  
            total = sum(float(item['price']) * item['quantity'] for item in cart_items)
            
            client = razorpay.Client(auth=("rzp_test_7kPo1SLPf8JLM2", "s3ZK5qrR1Vyl9LPldjAm3Kru"))
            payment=client.order.create({
            "amount": total*100,
            "currency": "INR",
            # "receipt": "receipt#1",
            # "partial_payment": false,
            # "notes": {
            #     "key1": "value3",
            #     "key2": "value2"
            # }
            })            
            response = render(request, 'ecom/payment.html',{'payment':payment})
            # response.set_cookie('email',email)
            response.set_cookie('name',name)
            response.set_cookie('mobile',mobile)
            # response.set_cookie('address',address)
            return response
    return render(request,'ecom/customer_address.html',{'addressForm':addressForm,'product_in_cart':product_in_cart,'product_count_in_cart':product_count_in_cart})




# here we are just directing to this view...actually we have to check whther payment is successful or not
#then only this view should be accessed
def payment_success_view(request):
    # Here we will place order | after successful payment
    # we will fetch customer  mobile, address, Email
    # we will fetch product id from cookies then respective details from db
    # then we will create order objects and store in db
    # after that we will delete cookies because after order placed...cart should be empty
    # customer=models.Customer.objects.get(user_id=request.user.id)
    products=None
    # email=None
    name=None
    mobile=None
    # address=None
    cart=request.session['cart']
    if cart:
        cartproducts = list(cart.values())
        products = models.Product.objects.filter(id__in=[item['id'] for item in cartproducts.values()])
            # Here we get products list that will be ordered by one customer at a time

    # these things can be change so accessing at the time of order...
    # if 'email' in request.COOKIES:
    #     email=request.COOKIES['email']
    if 'name' in request.COOKIES:
        name=request.COOKIES['name']    
    if 'mobile' in request.COOKIES:
        mobile=request.COOKIES['mobile']
    # if 'address' in request.COOKIES:
    #     address=request.COOKIES['address']

    # here we are placing number of orders as much there is a products
    # suppose if we have 5 items in cart and we place order....so 5 rows will be created in orders table
    # there will be lot of redundant data in orders table...but its become more complicated if we normalize it
    for product in products:
        models.Orders.objects.get_or_create(product=product,mobile=mobile,name=name)
        # customer=customer,,address=address,email=email,,status='Pending'

    # after order placed cookies should be deleted
    response = render(request,'ecom/payment_success.html')
    # response.delete_cookie('product_ids')
    del request.session['cart']
    # response.delete_cookie('email')
    response.delete_cookie('name')
    response.delete_cookie('mobile')
    # response.delete_cookie('address')
    return response

#---------------------------------------------------------------------------------
#------------------------ ABOUT US AND CONTACT US VIEWS START --------------------
#---------------------------------------------------------------------------------
def aboutus_view(request):
    return render(request,'ecom/aboutus.html')

def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name=sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            send_mail(str(name)+' || '+str(email),message, settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently = False)
            return render(request, 'ecom/contactussuccess.html')
    return render(request, 'ecom/contactus.html', {'form':sub})
