# Claims Management Application

## Overview

The Claims Management Application is a comprehensive Django-based system for managing insurance claims workflows. This application demonstrates the practical implementation of Django Steps, a reusable workflow management system for Django projects.

## Features

- Customer management
- Policy administration
- Claims processing with multi-step workflows
- Document management
- Payment processing
- Role-based access control

## Data Models

The application uses the following primary models:

- **Customer**: Represents policyholders who can submit claims
- **Policy**: Insurance policies belonging to customers
- **Claim**: Insurance claims filed by customers
- **ClaimNote**: Notes added during claim processing
- **ClaimPayment**: Payments made for approved claims

## Workflow Overview

The claims processing workflow typically follows these steps:

1. **Claim Submission**: Customer or agent submits a new claim
2. **Initial Review**: Claims adjuster reviews the claim details
3. **Investigation**: For complex claims, an investigation may be required
4. **Approval/Denial**: Supervisor reviews and approves or denies the claim
5. **Payment Processing**: For approved claims, payment is processed

## Testing the Workflow

This guide will walk you through testing the claims processing workflow from start to finish.

### Prerequisites

- Python 3.11.x installed
- Django installed
- Project dependencies installed

### Setting Up

1. Clone the repository and navigate to the project directory
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Navigate to the example directory:
   ```bash
   cd example
   ```
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Create a superuser for admin access:
   ```bash
   python manage.py createsuperuser
   ```
6. Start the development server:
   ```bash
   python manage.py runserver
   ```

### Testing the Claims Workflow

#### Step 1: Create a Customer

1. Log in to the admin interface at http://127.0.0.1:8000/admin/
2. Navigate to the Claims application section
3. Click on "Customers" and then "Add Customer"
4. Fill in the required information:
   - Name
   - Email
   - Phone (optional)
   - Address (optional)
5. Click "Save"

Alternatively, using the frontend:
1. Go to http://127.0.0.1:8000/claims/
2. Click on "Customers" in the navigation menu
3. Click "Add New Customer"
4. Fill out the form and submit

#### Step 2: Create a Policy

1. From the Customer detail page, click "Add Policy"
2. Fill in the policy details:
   - Policy Number (or let the system generate one)
   - Policy Type (Auto, Home, Health, or Life)
   - Start Date
   - End Date
   - Premium Amount
   - Coverage Amount
3. Click "Save"

#### Step 3: Submit a Claim

1. From the Policy detail page, click "Submit Claim"
2. Fill in the claim information:
   - Incident Date
   - Description of the incident
   - Amount Claimed
   - Priority (Low, Medium, High, Urgent)
   - Incident Location
   - Upload any supporting documents (optional)
3. Click "Submit"

#### Step 4: Initial Claim Review

1. Log in as a user with adjuster permissions
2. Go to the Claims List and find the newly submitted claim
3. Click on the claim to view details
4. If the claim is in the initial review stage, you'll see a "Start Review" button
5. Click "Start Review" to begin the formal review process
6. Once the claim moves to the review stage, a "Claim Review" form will be displayed
7. Fill in the review form:
   - Enter the approved amount
   - Add adjuster notes
8. Click "Submit Review"

#### Step 5: Claim Investigation (if needed)

1. If the claim requires investigation, it will show in the "Investigation" status
2. Click on the claim and then "Update Investigation"
3. Add investigation notes
4. Upload any evidence or documentation
5. Select the next workflow step (typically "Approval")
6. Click "Submit"

#### Step 6: Claim Approval/Denial

1. Log in as a user with supervisor permissions
2. Navigate to the claim in "Pending Approval" status
3. Click "Process Approval"
4. Review all claim details and notes
5. Enter the approved amount (if approving)
6. Add supervisor notes
7. Select "Approve" or "Deny"
8. Click "Submit Decision"

#### Step 7: Payment Processing (for approved claims)

1. Navigate to the approved claim
2. Click "Process Payment"
3. Fill in the payment details:
   - Payment Amount
   - Payment Date
   - Payment Method
   - Reference Number
   - Notes
4. Click "Process Payment"

### Testing Workflow Transitions

To test special workflow transitions:

#### Canceling a Claim

1. From any claim detail page, click "Cancel Claim"
2. Provide a reason for cancellation
3. Click "Confirm Cancellation"

#### Adding Notes

At any point in the workflow, you can add notes to the claim:

1. From the claim detail page, scroll to the "Add Note" section
2. Enter your note content
3. Check "Internal Note" if it should only be visible to staff
4. Click "Add Note"

### Viewing Workflow History

Each claim maintains a complete history of its workflow progression:

1. Open the claim detail page
2. Scroll to the "Workflow History" section
3. Review the timeline of all workflow transitions, including dates, users, and status changes

## Troubleshooting

### Common Issues

1. **Workflow Step Not Available**: Ensure you have the correct permissions for the action you're trying to perform

2. **Payment Processing Errors**: Verify that the claim has been properly approved before attempting payment

3. **File Upload Issues**: Check that your file types are supported and within the size limit

## Advanced Testing

### Using Management Commands

The application includes management commands for batch operations:

```bash
# Generate test data
python manage.py generate_test_data

# Check for stalled claims
python manage.py find_stalled_claims
```

### API Testing

If you're integrating with the application's API endpoints, you can test them using tools like curl or Postman:

```bash
# Example: Get all claims (with authentication)
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8000/api/claims/
```

## Conclusion

This guide covers the basics of testing the claims workflow. The application demonstrates the power and flexibility of the Django Steps workflow management system, allowing for complex business processes to be modeled and managed effectively.

For more information about the underlying workflow system, refer to the main project README and documentation.
