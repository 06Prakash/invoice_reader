import React, { useState, useEffect } from "react";
import axios from "axios";
import { useHistory } from "react-router-dom"; // Import useHistory for navigation
import './styles/PaymentPageComponent.css';

const PaymentPageComponent = () => {
    const [razorpayKey, setRazorpayKey] = useState(""); // Razorpay key
    const [amount, setAmount] = useState(""); // User-entered amount
    const [finalCredits, setFinalCredits] = useState(0.0); // Credits after fee deduction
    const [transactionFee, setTransactionFee] = useState(0.0); // Transaction fee
    const [loading, setLoading] = useState(false);
    const history = useHistory(); // For navigation

    // Fetch Razorpay key from backend
    useEffect(() => {
        const fetchRazorpayKey = async () => {
            try {
                const response = await axios.get("/razor/get-key", {
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem("jwt_token")}`,
                    },
                });
                setRazorpayKey(response.data.key);
            } catch (error) {
                console.error("Failed to fetch Razorpay key:", error);
                alert("Unable to fetch Razorpay key. Please try again later.");
            }
        };
        fetchRazorpayKey();

        if (!window.Razorpay) {
            console.error("Razorpay SDK failed to load. Please check your network connection.");
            alert("Payment integration is not available right now. Please try again later.");
        }
    }, []);

    // Calculate transaction fee and credits
    const handleAmountChange = (e) => {
        const enteredAmount = parseFloat(e.target.value) || 0;
        const fee = parseFloat((enteredAmount * 2) / 100).toFixed(2); // 2% transaction fee
        const credits = parseFloat((enteredAmount - fee) / 10).toFixed(2); // ₹10 = 1 credit

        setAmount(enteredAmount);
        setTransactionFee(parseFloat(fee));
        setFinalCredits(parseFloat(credits));
    };

    // Handle payment initiation
    const handlePayment = async () => {
        if (!amount || amount <= 0) {
            alert("Please enter a valid amount!");
            return;
        }

        if (amount < 10) {
            alert("Minimum payment amount is ₹10.");
            return;
        }

        if (!razorpayKey) {
            alert("Razorpay key is not available. Please try again later.");
            return;
        }

        setLoading(true);

        try {
            const response = await axios.post(
                "/razor/initiate-payment",
                { amount: amount },
                {
                    headers: {
                        Authorization: `Bearer ${localStorage.getItem("jwt_token")}`,
                    },
                }
            );

            const { id, amount: razorpayAmount, currency } = response.data;

            const options = {
                key: razorpayKey,
                amount: razorpayAmount,
                currency: currency,
                name: "NIRA: TRANSFORMING PDFS WITH CUTTING-EDGE AI",
                description: "Purchase Credits",
                order_id: id,
                handler: async function (response) {
                    console.log("Payment successful:", response);
                    try {
                        await axios.post(
                            "/razor/payment-success",
                            {
                                payment_id: response.razorpay_payment_id,
                                order_id: response.razorpay_order_id,
                                signature: response.razorpay_signature,
                                amount: razorpayAmount, // Include the correct amount in the payload
                            },
                            {
                                headers: {
                                    Authorization: `Bearer ${localStorage.getItem("jwt_token")}`,
                                },
                            }
                        );
                        alert("Payment successful and credits updated!");
                    } catch (error) {
                        console.error("Failed to update credits:", error);
                        alert("Payment successful, but credits update failed.");
                    }
                },
                prefill: {
                    name: "Your Name",
                    email: "user@example.com",
                    contact: "9999999999",
                },
                theme: {
                    color: "#3399cc",
                },
            };

            const razorpay = new window.Razorpay(options);
            razorpay.open();

            razorpay.on("payment.failed", function (response) {
                console.error("Payment failed:", response.error);
                alert("Payment failed: " + response.error.description);
            });
        } catch (error) {
            console.error("Payment initiation failed:", error);
            alert("Payment initiation failed.");
        } finally {
            setLoading(false);
        }
    };

    // Navigate back to the main page
    const handleGoBack = () => {
        history.push("/"); // Update the path to match your main page route
    };

    return (
        <div className="payment-page">
            <h2>Buy Credits</h2>

            <div className="payment-input">
                <label htmlFor="amount">Enter Amount (INR):</label>
                <input
                    type="number"
                    id="amount"
                    value={amount}
                    onChange={handleAmountChange}
                    disabled={loading}
                />
            </div>

            <div className="payment-summary">
                <p>Transaction Fee (2%): ₹{transactionFee.toFixed(2)}</p>
                <p>Credits You Will Receive: {finalCredits.toFixed(2)}</p>
            </div>

            <button onClick={handlePayment} disabled={loading}>
                {loading ? "Processing..." : `Pay ₹${amount}`}
            </button>

            <button onClick={handleGoBack} disabled={loading} className="go-back-button">
                Go Back
            </button>
        </div>
    );
};

export default PaymentPageComponent;
